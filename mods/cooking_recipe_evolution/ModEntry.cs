using StardewModdingAPI;
using StardewModdingAPI.Events;
using StardewValley;

namespace cooking_recipe_evolution;

public class ModEntry : Mod
{
    public static RecipeProgress Progress = new();

    public override void Entry(IModHelper helper)
    {
        helper.Events.GameLoop.SaveLoaded += (_, _) =>
            Progress = helper.Data.ReadSaveData<RecipeProgress>("recipe-progress") ?? new();
        helper.Events.GameLoop.ReturnedToTitle += (_, _) => helper.Data.WriteSaveData("recipe-progress", Progress);
        helper.Events.Player.CookingRecipeAssembled += OnCooked;
    }

    private void OnCooked(object? sender, PlayerCookedRecipeEventArgs e)
    {
        string id = e.RecipeId;
        int count = Progress.Bump(id);
        int tier = count / 15;                       // every 15 cooks -> tier up
        if (tier > 0 && tier <= 3 && Progress.NotifyTier(id, tier))
        {
            string evolved = Evolutions.EvolvedId(Helper, id, tier);
            Game1.cookingRecipes.TryAdd(evolved, 0);
            Game1.addHUDMessage(new HUDMessage($"Рецепт улучшился: {evolved}!", HUDMessage.help_type));
        }
    }
}

/// <summary>Maps a base recipe to its evolved names via data/evolutions.json.</summary>
internal static class Evolutions
{
    public static string EvolvedId(IModHelper helper, string recipeId, int tier)
    {
        var data = helper.Data.ReadJsonFile<Dictionary<string, TierList>>("data/evolutions.json");
        if (data is not null && data.TryGetValue(recipeId, out var tiers) && tier <= tiers.Tiers.Count)
            return tiers.Tiers[tier - 1];
        return $"{recipeId}+{tier}";
    }

    private record TierList(List<string> Tiers);
}

internal class RecipeProgress
{
    public Dictionary<string, int> Counts { get; set; } = new();
    public HashSet<string> Announced { get; set; } = new();
    public int Bump(string id) { Counts[id] = Counts.GetValueOrDefault(id) + 1; return Counts[id]; }
    public bool NotifyTier(string id, int tier) => Announced.Add($"{id}:{tier}");
}
