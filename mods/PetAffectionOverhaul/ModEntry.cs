using StardewModdingAPI;
using StardewModdingAPI.Events;
using StardewValley;

namespace PetAffectionOverhaul;

public class ModEntry : Mod
{
    private FriendshipStore _store = new();

    public override void Entry(IModHelper helper)
    {
        helper.Events.GameLoop.SaveLoaded += (_, _) =>
            _store = helper.Data.ReadSaveData<FriendshipStore>("pet-affection") ?? new();
        helper.Events.GameLoop.TimeChanged += OnTimeChanged;
        helper.Events.GameLoop.ReturnedToTitle += (_, _) =>
            helper.Data.WriteSaveData("pet-affection", _store);
    }

    private void OnTimeChanged(object? sender, TimeChangedEventArgs e)
    {
        var pet = Game1.player.getPet();
        if (pet is null) return;

        // Passive affection gain when the pet is fed; buffs scale with hearts
        int hearts = _store.Hearts(pet.Name);
        switch (pet.Type)
        {
            case "Cat": CrowScare.ApplyRadius(hearts); break;
            case "Dog": TruffleBoost.ApplyChance(hearts); break;
        }
    }
}

internal class FriendshipStore
{
    public Dictionary<string, int> Affection { get; set; } = new();
    public int Hearts(string petName) => Math.Clamp(Affection.GetValueOrDefault(petName, 0) / 250, 0, 5);
    public void Add(string petName, int pts) => Affection[petName] = Affection.GetValueOrDefault(petName) + pts;
}

/// <summary>Harmony anchors for per-pet buffs (implemented in a follow-up pass).</summary>
internal static class CrowScare
{
    /// <summary>Cats within radius prevent crow events on the farm.</summary>
    public static void ApplyRadius(int hearts) { /* patch Farm.spawnCritters */ }
}

internal static class TruffleBoost
{
    /// <summary>Dogs increase truffle-finding chance on rainy forest walks.</summary>
    public static void ApplyChance(int hearts) { /* patch Farmer.findTruffles */ }
}
