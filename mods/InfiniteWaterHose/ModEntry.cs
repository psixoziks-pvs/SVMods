using StardewModdingAPI;
using StardewModdingAPI.Events;
using StardewValley;
using StardewValley.Tools;

namespace InfiniteWaterHose;

public class ModEntry : Mod
{
    public const string HoseId = "(O)mods.hose.infinite";
    private static bool _anchored;

    public override void Entry(IModHelper helper)
    {
        helper.Events.Content.AssetRequested += OnAssetRequested;
        helper.Events.GameLoop.SaveLoaded += (_, _) => _anchored = false;
        helper.Events.Input.ButtonPressed += OnButton;
        helper.Events.GameLoop.UpdateTicked += OnTick;
    }

    private void OnAssetRequested(object? sender, AssetRequestedEventArgs e)
    {
        if (e.NameWithoutLocale.IsEquivalentTo("Data/Tools"))
            e.Edit(asset => asset.AsDictionary<string, string>().Data[HoseId] =
                "Бесконечный шланг|60|900|false|wateringCan");
        if (e.NameWithoutLocale.IsEquivalentTo("Data/Shops"))
            e.Edit(asset =>
            {
                var d = asset.AsDictionary<string, string>().Data;
                d["SeedShop"] += $"/{HoseId} 250 -1 -1 -1";   // Pierre, 250 gold, always in stock
            });
    }

    private void OnButton(object? sender, ButtonPressedEventArgs e)
    {
        if (!Context.IsWorldReady) return;
        var held = Game1.player.CurrentObjectIndex >= 0 ? Game1.player.items.CurrentItem : null;
        bool holdingHose = held?.QualifiedItemId == HoseId || held?.Name == "Infinite Water Hose";
        if (!holdingHose || !e.Button.Equals(SButton.MouseLeft)) return;

        // First click in water anchors the source end; later clicks water tiles remotely
        var tile = e.Cursor.GrabTile;
        if (!_anchored && Game1.currentLocation.doesTileHaveProperty(tile.X, tile.Y, "Water", "Back") is not null)
        {
            _anchored = true;
            Game1.drawObjectDialogue(Helper.Translation.Get("anchor.msg"));
        }
        else if (_anchored)
            WaterTile(Game1.currentLocation, new Vector2i(tile.X, tile.Y));
    }

    private static void WaterTile(GameLocation loc, Vector2i tile)
    {
        if (loc.doesTileHaveProperty(tile.X, tile.Y, "Diggable", "Back") is null) return;
        var feature = loc.terrainFeatures.Get(tile)?.asCrop();
        if (feature is not null && !feature.hasWater.Value)
            feature.hasWater.Value = true;
        Game1.playSound("wateringCan");
    }

    private void OnTick(object? sender, UpdateTickedEventArgs e) { /* drag hose trail rendering */ }
}
