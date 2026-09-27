using HarmonyLib;
using StardewModdingAPI;
using StardewModdingAPI.Events;
using StardewValley;
using StardewValley.Menus;

namespace InstantFishing;

public class ModEntry : Mod
{
    private static Config _cfg = new();

    public override void Entry(IModHelper helper)
    {
        _cfg = helper.ReadConfig<Config>();
        if (!_cfg.Enabled) return;
        Harmony.CreateAndPatchAll(typeof(ModEntry).Assembly, helper.Reflection.GetAssemblyId());
    }

    /// <summary>Replace the timed fishing bar with an instant success roll.</summary>
    [HarmonyPatch(typeof(FishingBar), nameof(FishingBar.receiveLeftClick))]
    private static void SkipBar(FishingBar __instance)
    {
        __instance.SetCaught(true, perfect: _cfg.AlwaysPerfect);
        Game1.activeClickableMenu = null;
        Game1.playSound("fishTrap");
    }
}

internal class Config
{
    public bool Enabled { get; set; } = true;
    public bool AlwaysPerfect { get; set; } = false;
    public bool ShowCatchToast { get; set; } = true;
}
