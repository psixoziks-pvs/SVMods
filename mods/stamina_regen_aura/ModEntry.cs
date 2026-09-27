using StardewModdingAPI;
using StardewModdingAPI.Events;
using Microsoft.Xna.Framework;
using StardewValley;

namespace stamina_regen_aura;

public class ModEntry : Mod
{
    private Config _config = new();

    public override void Entry(IModHelper helper)
    {
        _config = helper.ReadConfig<Config>();
        helper.Events.GameLoop.UpdateTicked += OnUpdateTicked;
    }

    private void OnUpdateTicked(object? sender, UpdateTickedEventArgs e)
    {
        if (!Context.IsWorldReady || !e.IsMultipleOf(60)) return;   // once per second
        if (!IsInAuraRange()) return;

        Game1.player.Stamina = Math.Min(Game1.player.MaxStamina, Game1.player.Stamina + _config.RegenPerSecond);
    }

    /// <summary>True when an aura totem is placed within the configured radius.</summary>
    private bool IsInAuraRange()
    {
        foreach (var pair in Game1.currentLocation.objects)
        {
            var o = pair.Value;
            if (o is not null && o.Name == "aura_totem"
                && Vector2.Distance(Game1.player.Position, o.Position) <= _config.Radius * 64f)
                return true;
        }
        return false;
    }
}

internal class Config
{
    public int RegenPerSecond { get; set; } = 2;
    public int Radius { get; set; } = 6;
}
