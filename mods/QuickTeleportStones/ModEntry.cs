using StardewModdingAPI;
using StardewModdingAPI.Events;
using StardewValley;
using StardewValley.ItemTypeDefinitions;

namespace QuickTeleportStones;

public class ModEntry : Mod
{
    public const string StoneId = "(O)mods.quicktp.stone";

    public override void Entry(IModHelper helper)
    {
        helper.Events.Content.AssetRequested += OnAssetRequested;
        helper.Events.GameLoop.SaveLoaded += OnSaveLoaded;
        helper.Events.Input.ButtonPressed += OnButtonPressed;
    }

    private void OnAssetRequested(object? sender, AssetRequestedEventArgs e)
    {
        if (e.NameWithoutLocale.IsEquivalentTo("Data/Objects"))
            e.Edit(asset =>
            {
                var model = asset.AsDictionary<string, string>().Data;
                model["mods.quicktp.stone"] =
                    "Teleport Stone|900|-20|Basic||false|Quick Teleport Stone. Right-click to warp.|0||assets/stone.png||||";
            });
    }

    private void OnSaveLoaded(object? sender, SaveLoadedEventArgs e)
    {
        string json = Helper.Data.ReadSaveData<string>("quicktp-bindings") ?? "{}";
        WarpRegistry.Load(json);
    }

    private void OnButtonPressed(object? sender, ButtonPressedEventArgs e)
    {
        if (!Context.IsWorldReady) return;
        var held = Game1.player.items.CurrentItem;
        if (held is not null && held.QualifiedItemId.StartsWith("(BC)") == false &&
            e.Button.Equals(SButton.Right) && WarpRegistry.BoundStones.ContainsKey(held.Name))
        {
            var target = WarpRegistry.BoundStones[held.Name];
            Game1.warpFarmer(target.Location, target.X, target.Y, false);
            Game1.playSound("teleport");
        }
    }
}

internal record WarpTarget(string Location, int X, int Y);

internal static class WarpRegistry
{
    public static Dictionary<string, WarpTarget> BoundStones { get; } = new();
    public static void Load(string json) { /* deserialized bindings */ }
}
