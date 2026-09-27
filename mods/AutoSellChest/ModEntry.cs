using Microsoft.Xna.Framework;
using StardewModdingAPI;
using StardewModdingAPI.Events;
using StardewValley;

namespace AutoSellChest;

/// <summary>Entrypoint for the Auto-Sell Chest mod.</summary>
public class ModEntry : Mod
{
    private Config _config = new();

    public override void Entry(IModHelper helper)
    {
        _config = helper.ReadConfig<Config>();
        helper.Events.GameLoop.SaveLoaded += OnSaveLoaded;
        helper.Events.Input.ButtonPressed += OnButtonPressed;
    }

    private void OnSaveLoaded(object? sender, SaveLoadedEventArgs e)
    {
        Monitor.Log("Auto-Sell Chest loaded. Press U near a tagged chest to sell its contents.", LogLevel.Info);
    }

    private void OnButtonPressed(object? sender, ButtonPressedEventArgs e)
    {
        if (!Context.IsWorldReady || !e.Button.Equals(SButton.U)) return;

        var chest = GetPlayerNearbyChest();
        if (chest is null) return;

        int total = 0;
        for (int i = chest.Items.Count - 1; i >= 0; i--)
        {
            var item = chest.Items[i];
            if (item is null || !_config.DeniedItems.Contains(item.Name)) continue; // filter
            int price = (int)(item.Price * (1 + _config.SellPriceBonusPercent / 100.0));
            Game1.player.Money += price;
            total += price;
            chest.Items.RemoveAt(i);
        }
        if (total > 0)
            Game1.drawObjectDialogue($"Auto-sold items for {total}g.");
    }

    private static Chest? GetPlayerNearbyChest()
    {
        foreach (var off in new[] { new Point(0, 1), new Point(1, 0), new Point(-1, 0), new Point(0, -1) })
        {
            var tile = Game1.player.TilePoint + off;
            if (Game1.currentLocation.getObjectAtTile(tile.X, tile.Y) is Chest { Tag: "mod.AutoSellChest" } ch)
                return ch;
        }
        return null;
    }
}

internal class Config
{
    public int SellPriceBonusPercent { get; set; } = 5;
    public List<string> DeniedItems { get; set; } = new() { "Wood", "Stone" };
    public int MaxSellPerDay { get; set; } = 9999;
}
