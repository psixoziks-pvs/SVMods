using HarmonyLib;
using StardewValley;

namespace CropRotationBonus;

/// <summary>Harmony patches that apply the rotation modifier to harvest quality/yield.</summary>
[HarmonyPatch(typeof(Crop), nameof(Crop.harvest))]
internal static class HarvestPatch
{
    static void Prefix(Crop __instance, GameLocation __location)
    {
        var key = SoilLedger.Key(__location, __instance.tileX.Value, __instance.tileY.Value);
        var fam = CropFamilies.FamilyOf(__instance);
        __instance.farmingLevel.Value = Math.Max(0, (int)(__instance.farmingLevel.Value * ModEntry.Ledger.Modifier(key, fam)));
    }

    static void Postfix(Crop __instance, GameLocation __location)
    {
        ModEntry.Ledger.Record(SoilLedger.Key(__location, __instance.tileX.Value, __instance.tileY.Value),
                               CropFamilies.FamilyOf(__instance));
    }
}

internal static class CropFamilies
{
    public static string FamilyOf(Crop crop) => crop.indexOfHarvest.Value switch
    {
        >= 394 and <= 421 => "berry",
        >= 270 and <= 281 => "root",
        _ => "generic",
    };
}
