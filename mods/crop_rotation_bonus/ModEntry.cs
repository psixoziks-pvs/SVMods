using StardewModdingAPI;
using StardewModdingAPI.Events;
using StardewValley;

namespace crop_rotation_bonus;

public class ModEntry : Mod
{
    internal static SoilLedger Ledger = new();

    public override void Entry(IModHelper helper)
    {
        helper.Events.GameLoop.SaveLoaded += (_, _) =>
            Ledger = helper.Data.ReadSaveData<SoilLedger>("rotation-ledger") ?? new();
        helper.Events.GameLoop.ReturnedToTitle += (_, _) => helper.Data.WriteSaveData("rotation-ledger", Ledger);
    }
}

internal class SoilLedger
{
    // key = "Farm_60_15" -> history of crop families
    public Dictionary<string, List<string>> History { get; set; } = new();

    public static string Key(GameLocation loc, int x, int y) => $"{loc.NameOrUniqueName}_{x}_{y}";

    public void Record(string key, string family)
    {
        if (!History.TryGetValue(key, out var h)) History[key] = h = new();
        h.Add(family);
        if (h.Count > 4) h.RemoveAt(0);
    }

    /// <summary>+15% per consecutive different family, -20% for repeats.</summary>
    public float Modifier(string key, string family)
    {
        if (!History.TryGetValue(key, out var h) || h.Count == 0) return 1f;
        return h[^1] == family ? 0.8f : Math.Min(1.6f, 1f + 0.15f * h.Count);
    }
}
