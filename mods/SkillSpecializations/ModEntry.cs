using StardewModdingAPI;
using StardewModdingAPI.Events;
using StardewValley;

namespace SkillSpecializations;

public class ModEntry : Mod
{
    public static SpecStore Specs = new();

    public override void Entry(IModHelper helper)
    {
        helper.Events.GameLoop.SaveLoaded += (_, _) =>
            Specs = helper.Data.ReadSaveData<SpecStore>("specializations") ?? new();
        helper.Events.GameLoop.ReturnedToTitle += (_, _) => helper.Data.WriteSaveData("specializations", Specs);
        helper.Events.Player.LevelChanged += OnLevelChanged;
    }

    private void OnLevelChanged(object? sender, LevelChangedEventArgs e)
    {
        if (!e.IsLocalPlayer) return;
        int lvl = e.NewLevel;
        if (lvl is 5 or 10)
            Menu.OpenFor(e.Skill.ToString(), lvl, Helper, Specs);
    }
}

internal class SpecStore
{
    public Dictionary<string, string> Chosen { get; set; } = new(); // "Fishing-5" -> "DeepSea"
    public bool Has(string key) => Chosen.ContainsKey(key);
}

internal static class Menu
{
    public static void OpenFor(string skill, int level, IModHelper helper, SpecStore store)
    {
        var options = SpecData.For(skill, level);
        if (options.Count == 0) return;
        Game1.activeClickableMenu = new ChoiceMenu(skill, level, options, choice =>
        {
            store.Chosen[$"{skill}-{level}"] = choice.Id;
            Game1.drawObjectDialogue(helper.Translation.Get("chosen", new { spec = choice.Name }));
        });
    }
}

/// <summary>Loads specialization options from data/specializations.json.</summary>
internal static class SpecData
{
    private static readonly Dictionary<string, List<SpecOption>> Cache = new();

    public static List<SpecOption> For(string skill, int level) =>
        Cache.TryGetValue($"{skill}:{level}", out var list) ? list : new();

    public static void Populate(IModHelper helper)
    {
        var raw = helper.Data.ReadJsonFile<Dictionary<string, Dictionary<string, List<SpecDto>>>>("data/specializations.json");
        if (raw is null) return;
        foreach (var (skill, tiers) in raw)
            foreach (var (level, opts) in tiers)
                Cache[$"{skill}:{level}"] = opts.Select(o => new SpecOption(o.Id, o.Name, o.Perks[0])).ToList();
    }

    private record SpecDto(string Id, string Name, List<string> Perks);
}
