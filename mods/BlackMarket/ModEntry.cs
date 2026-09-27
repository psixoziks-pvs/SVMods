using StardewModdingAPI;
using StardewModdingAPI.Events;
using StardewValley;

namespace BlackMarket;

public class ModEntry : Mod
{
    private NPC? _merchant;

    public override void Entry(IModHelper helper)
    {
        helper.Events.GameLoop.TimeChanged += OnTimeChanged;
        helper.Events.GameLoop.DayStarted += (_, _) => _spawnedToday = false;
    }

    private bool _spawnedToday;

    private void OnTimeChanged(object? sender, TimeChangedEventArgs e)
    {
        if (_spawnedToday || !Context.IsWorldReady) return;
        var cfg = Helper.ReadConfig<Config>();
        if (e.NewTime < cfg.SpawnTime || !Game1.isRaining) return;
        if (Game1.random.NextDouble() > cfg.SpawnChance) return;

        SpawnMerchant(cfg);
        _spawnedToday = true;
    }

    private void SpawnMerchant(Config cfg)
    {
        var dialogue = new Dialogue(null, Helper.Translation.Get("merchant.greeting"), "blackMerchant");
        _merchant = new NPC(dialogue, new xTile.Dimensions.Location(20 * 64, 18 * 64), Game1.getFarm(),
                            "mods.blackmarket", null, "blackMerchant");
        Game1.getFarm().addCharacter(_merchant);
        Game1.showRedMessage(Helper.Translation.Get("spawn.msg"));
    }

    /// <summary>Shop opening is handled via a GameLoop menu patch reading data/shop.json.</summary>
    internal static class Notes { }
}

internal class Config
{
    public int SpawnTime { get; set; } = 2000;
    public double SpawnChance { get; set; } = 0.6;
    public string ShopDataPath { get; set; } = "data/shop.json";
}
