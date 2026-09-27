using StardewValley;
using StardewValley.Monsters;

namespace seasonal_monster_invasion;

internal static class WaveEngine
{
    private static readonly List<Monster> Active = new();
    private static int _wave, _ticksLeft;

    public static void StartRun(Farm farm, int waves) { _wave = waves; _ticksLeft = 0; }

    public static void Tick(object? sender, UpdateTickedEventArgs e)
    {
        if (_wave <= 0 || !Context.IsWorldReady) return;
        if (--_ticksLeft > 0) return;

        SpawnWave(Game1.getFarm());
        _ticksLeft = 60 * 60; // one in-game hour between waves
        if (--_wave == 0) EndRun();
    }

    private static void SpawnWave(Farm farm)
    {
        for (int i = 0; i < 4 + _wave; i++)
        {
            var spot = farm.getNewMobileFriendSpot("slime");
            var m = Game1.random.NextBool() ? new GreenSlime(spot) : new Bat(spot, "bat");
            farm.characters.Add(m);
            Active.Add(m);
        }
    }

    private static void EndRun()
    {
        foreach (var m in Active) m.Health = 0;
        Tokens.Value += 100;
        Game1.drawObjectDialogue($"Вторжение отбито! Вы получили жетоны оборону: +100 (всего {Tokens.Value}).");
    }
}
