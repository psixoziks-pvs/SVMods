using StardewValley;

namespace CommunityBoard2;

internal record Contract(string Id, string Type, string Target, int Quantity, int RewardGold, int DeadlineDays, string Giver);

internal static class PlayerProfile
{
    public static Profile Capture() => new(
        Game1.player.FarmingLevel, Game1.player.MiningLevel, Game1.player.CombatLevel,
        Game1.player.NetworkGetPendingMessages.Length, Game1.player.money);

    internal record Profile(int Farming, int Mining, int Combat, int Pending, int Money);
}

internal static class Rng
{
    public static Random Seeded(int day) => new(day * 7919 + Game1.uniqueIDForThisGame.GetHashCode());
}

internal static class Generator
{
    public static Contract Generate(PlayerProfile.Profile p, Random rng)
    {
        string[] types = ["fetch", "delivery", "cull"];
        string type = types[rng.Next(types.Length)];
        int qty = Math.Clamp(rng.Next(3, 12) + p.Farming / 2, 1, 30);
        int reward = 150 + qty * 40 + rng.Next(0, 200);
        return type switch
        {
            "fetch"    => new Contract(NewId(rng), type, CommonSeeds(rng), qty, reward, 3, RandomVillager(rng)),
            "cull"     => new Contract(NewId(rng), type, MonsterForLevel(p), qty, reward, 2, "Adventurer Guild"),
            _          => new Contract(NewId(rng), type, "to:" + RandomVillager(rng), 1, reward, 1, "Mayor Lewis"),
        };
    }

    private static string NewId(Random r) => $"CB-{r.Next(1000, 9999)}";
    private static string CommonSeeds(Random r) => new[] { "cauliflower", "kale", "wheat", "corn" }[r.Next(4)];
    private static string MonsterForLevel(PlayerProfile.Profile p) => p.Combat >= 7 ? "Shadow Shaman" : "Green Slime";
    private static string RandomVillager(Random r) => Game1.getCharacterFromName("Abigail")?.name ??
        new[] { "Pierre", "Robin", "Marnie", "Caroline", "Sebastian" }[r.Next(5)];
}
