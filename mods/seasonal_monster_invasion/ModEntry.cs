using StardewModdingAPI;
using StardewModdingAPI.Events;
using StardewValley;

namespace seasonal_monster_invasion;

public class ModEntry : Mod
{
    public override void Entry(IModHelper helper)
    {
        helper.Events.GameLoop.TimeChanged += OnTimeChanged;
        helper.Events.GameLoop.UpdateTicked += WaveEngine.Tick;
        helper.Events.GameLoop.SaveLoaded += (_, _) =>
            Tokens.Load(helper.Data.ReadSaveData<int>("invasion-tokens") ?? 0);
        helper.Events.GameLoop.ReturnedToTitle += (_, _) => helper.Data.WriteSaveData("invasion-tokens", Tokens.Value);
    }

    private void OnTimeChanged(object? sender, TimeChangedEventArgs e)
    {
        if (e.NewTime != 2200 || !Context.IsWorldReady) return;
        if (!InvasionCalendar.IsInvasionTonight(Game1.currentSeason, Game1.dayOfMonth)) return;
        WaveEngine.StartRun(Game1.getFarm(), waves: 5 + Game1.year);
        Game1.playSound("newRecord");
        Game1.addHUDMessage(new HUDMessage("Ночь вторжения началась! Защищайте ферму!", HUDMessage.newQuest_type));
    }
}

internal static class Tokens { public static int Value; public static void Load(int v) => Value = v; }
