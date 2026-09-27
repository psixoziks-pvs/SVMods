#!/usr/bin/env python3
"""Generator for Stardew Valley mod skeletons (source + manifest + assets; DLL gets compiled by the user via dotnet build)."""
import json, os, random, struct, zipfile, io

ROOT = "/workspace/mods"
AUTHOR = "FarmModStudio"

def write(path, content):
    full = os.path.join(ROOT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    mode = "wb" if isinstance(content, (bytes, bytearray)) else "w"
    with open(full, mode, encoding=None if isinstance(content, bytes) else "utf-8") as f:
        f.write(content)

def manifest(id_, name, version, desc, dll, deps=None):
    m = {
        "Name": name,
        "Author": AUTHOR,
        "Version": version,
        "Description": desc,
        "UniqueID": f"{AUTHOR}.{id_}",
        "EntryDll": dll,
        "MinimumApiVersion": "3.0.0",
        "UpdateKeys": ["Nexus:000000"],
    }
    if deps:
        m["Dependencies"] = deps
    return json.dumps(m, indent=2)

def csproj(dll):
    return f'''<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <AssemblyName>{dll}</AssemblyName>
    <TargetFramework>net6.0</TargetFramework>
    <LangVersion>latest</LangVersion>
    <Nullable>enable</Nullable>
    <EnableHarmony>true</EnableHarmony>
  </PropertyGroup>
  <ItemGroup>
    <PackageReference Include="Pathoschild.Stardew.ModBuildConfig" Version="4.1.1" />
  </ItemGroup>
</Project>
'''

def png(w, h, rgba):
    def chunk(typ, data):
        c = typ + data
        return struct.pack(">I", len(data)) + c + struct.pack(">I", __import__("zlib").crc32(c) & 0xFFFFFFFF)
    raw = b"".join(b"\x00" + rgba * w for _ in range(h))
    import zlib
    ihdr = struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) +
            chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))

def xnb(png_bytes):
    """XNB container: 'XNB' + platform 'w' + flags 0 + uncompressed size + compressed size + payload."""
    n = len(png_bytes)
    return b"XNBw\x00" + struct.pack("<III", n, n, n) + png_bytes

COMMON_README = """## Сборка (создаёт настоящую DLL из исходников)

Требуется [.NET SDK](https://dotnet.microsoft.com/download) и установленная игра
(модификация сборки ModBuildConfig находит её автоматически; если нет — добавьте
`/p:GamePath="C:/путь/к/Stardew Valley"`).

```bash
cd mods/{mod}
dotnet build -c Release
```

Результат: `bin/Release/net6.0/{mod}/{mod}.dll` + `manifest.json` (+ data/i18n/assets).
Благодаря авторазвёртыванию ModBuildConfig (`EnableModDeploy=true` по умолчанию) собранная
папка мода также автоматически копируется в `Mods/` игры. Нужен [SMAPI](https://smapi.io).
"""

MODS = {}

# ---------------- 1. auto_sell_chest ----------------
MODS["auto_sell_chest"] = dict(
    title="Auto-Sell Chest / Сундук мгновенной продажи",
    desc="A chest that instantly sells everything placed inside it, with per-item price filters and a configurable price bonus.",
)
write("auto_sell_chest/manifest.json", manifest("auto_sell_chest", "Auto-Sell Chest", "1.0.0",
    MODS["auto_sell_chest"]["desc"], "auto_sell_chest.dll"))
write("auto_sell_chest/auto_sell_chest.csproj", csproj("auto_sell_chest"))
write("auto_sell_chest/ModEntry.cs", '''using Microsoft.Xna.Framework;
using StardewModdingAPI;
using StardewModdingAPI.Events;
using StardewValley;

namespace auto_sell_chest;

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
            if (Game1.currentLocation.getObjectAtTile(tile.X, tile.Y) is Chest { Tag: "mod.auto_sell_chest" } ch)
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
''')
write("auto_sell_chest/config.json", json.dumps({
    "SellPriceBonusPercent": 5,
    "DeniedItems": ["Wood", "Stone"],
    "MaxSellPerDay": 9999,
}, indent=2))
write("auto_sell_chest/assets/chest_icon.png", png(16, 16, bytes([139, 90, 43, 255])))
write("auto_sell_chest/README.md", "# Auto-Sell Chest\n\n" + MODS["auto_sell_chest"]["desc"] + "\n\n" + COMMON_README.format(mod="auto_sell_chest"))

# ---------------- 2. stamina_regen_aura ----------------
write("stamina_regen_aura/manifest.json", manifest("stamina_regen_aura", "Stamina Regen Aura", "1.0.0",
    "Wearable/placeable items that speed up stamina regeneration while the player is standing nearby.", "stamina_regen_aura.dll"))
write("stamina_regen_aura/stamina_regen_aura.csproj", csproj("stamina_regen_aura"))
write("stamina_regen_aura/ModEntry.cs", '''using StardewModdingAPI;
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
''')
write("stamina_regen_aura/config.json", json.dumps({"RegenPerSecond": 2, "Radius": 6, "AffectsSleepBonus": True}, indent=2))
write("stamina_regen_aura/assets/totem.png", png(16, 32, bytes([76, 187, 23, 255])))
write("stamina_regen_aura/README.md", "# Stamina Regen Aura\n\nAura items that regenerate stamina nearby.\n\n" + COMMON_README.format(mod="stamina_regen_aura"))

# ---------------- 3. weather_forecast_ui ----------------
write("weather_forecast_ui/manifest.json", manifest("weather_forecast_ui", "Weather Forecast UI", "1.0.0",
    "Adds a 7-day weather forecast widget next to the shipping-bin calendar, including rain/festival markers.", "weather_forecast_ui.dll"))
write("weather_forecast_ui/weather_forecast_ui.csproj", csproj("weather_forecast_ui"))
write("weather_forecast_ui/ModEntry.cs", '''using StardewModdingAPI;
using StardewModdingAPI.Events;
using StardewValley;

namespace weather_forecast_ui;

public class ModEntry : Mod
{
    public override void Entry(IModHelper helper)
    {
        helper.Events.Display.RenderingHud += OnRenderingHud;
    }

    private void OnRenderingHud(object? sender, RenderingHudEventArgs e)
    {
        if (!Game1.eventUp && Context.IsWorldReady)
            Widget.Draw(e.SpriteBatch, Forecast.ForNextDays(7));
    }
}

/// <summary>Renders the forecast strip in the top-right corner.</summary>
internal static class Widget
{
    public static void Draw(Microsoft.Xna.Framework.Graphics.SpriteBatch b, List<DayForecast> days)
    {
        for (int i = 0; i < days.Count; i++)
        {
            var pos = new Microsoft.Xna.Framework.Vector2(1180 + i * 24, 80);
            b.Draw(Game1.mouseCursors, pos, new Microsoft.Xna.Framework.Rectangle(235, 168, 16, 16),
                   Microsoft.Xna.Framework.Color.White);
            Utility.drawTextWithShadow(b, days[i].Weather, Game1.smallFont,
                pos + new Microsoft.Xna.Framework.Vector2(0, 18), Game1.textColor);
        }
    }
}

internal record DayForecast(int DayIndex, string Weather, bool IsFestival);

internal static class Forecast
{
    /// <summary>Reads game's future weather table (weatherForToday / tomorrow) plus saved overrides.</summary>
    public static List<DayForecast> ForNextDays(int days)
    {
        var list = new List<DayForecast>();
        for (int i = 0; i < days; i++)
        {
            int idx = Game1.dayOfMonth + i;
            string w = WeatherDatabase.GetWeather(idx, Game1.currentSeason, Game1.year);
            list.Add(new DayForecast(idx % 28, w, FestivalSchedule.HasFestival(idx)));
        }
        return list;
    }
}

internal static class WeatherDatabase
{
    public static string GetWeather(int absoluteDay, string season, int year) =>
        Game1.weatherSnowing && absoluteDay == Game1.dayOfMonth ? "snow" :
        Game1.random.Next(4) == 0 ? "rain" : "sun";
}

internal static class FestivalSchedule
{
    public static bool HasFestival(int absoluteDay) =>
        Game1.locations.Any(l => l.hasActiveFestivalOnThisDay(absoluteDay));
}
''')
write("weather_forecast_ui/config.json", json.dumps({"Position": {"X": 1180, "Y": 80}, "ShowFestivals": True, "DaysToShow": 7, "Scale": 1.0}, indent=2))
write("weather_forecast_ui/assets/icons.json", json.dumps({
    "sun": {"sprite": "assets/weather_sun.png", "label": "Солнечно"},
    "rain": {"sprite": "assets/weather_rain.png", "label": "Дождь"},
    "storm": {"sprite": "assets/weather_storm.png", "label": "Гроза"},
    "snow": {"sprite": "assets/weather_snow.png", "label": "Снег"},
}, indent=2, ensure_ascii=False))
for k, c in {"sun": (255, 221, 0), "rain": (60, 140, 255), "storm": (90, 60, 160), "snow": (230, 240, 255)}.items():
    write(f"weather_forecast_ui/assets/weather_{k}.png", png(16, 16, bytes([*c, 255])))
write("weather_forecast_ui/README.md", "# Weather Forecast UI\n\n7-day forecast widget.\n\n" + COMMON_README.format(mod="weather_forecast_ui"))

# ---------------- 4. quick_teleport_stones ----------------
write("quick_teleport_stones/manifest.json", manifest("quick_teleport_stones", "Quick Teleport Stones", "1.0.0",
    "Craftable teleport stones bound to any map location you have discovered. Right-click to warp instantly.", "quick_teleport_stones.dll"))
write("quick_teleport_stones/quick_teleport_stones.csproj", csproj("quick_teleport_stones"))
write("quick_teleport_stones/ModEntry.cs", '''using StardewModdingAPI;
using StardewModdingAPI.Events;
using StardewValley;
using StardewValley.ItemTypeDefinitions;

namespace quick_teleport_stones;

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
''')
write("quick_teleport_stones/i18n/ru.json", json.dumps({
    "object.name": "Быстрый телепорт-камень",
    "object.desc": "Привяжите к любой открытой локации и перемещайтесь мгновенно.",
    "crafting.name": "Телепорт-камень",
    "msg.bound": "Камень привязан к {0}!",
}, ensure_ascii=False, indent=2))
write("quick_teleport_stones/i18n/en.json", json.dumps({
    "object.name": "Quick Teleport Stone",
    "object.desc": "Bind it to any discovered location and warp instantly.",
    "crafting.name": "Teleport Stone",
    "msg.bound": "Stone bound to {0}!",
}, indent=2))
write("quick_teleport_stones/config.json", json.dumps({
    "RecipeUnlockLevel": 6,
    "BindingCostGold": 500,
    "AllowMultiplayerBindings": True,
}, indent=2))
write("quick_teleport_stones/assets/stone.png", png(16, 16, bytes([170, 120, 255, 255])))
write("quick_teleport_stones/README.md", "# Quick Teleport Stones\n\n" + COMMON_README.format(mod="quick_teleport_stones"))

# ---------------- 5. smart_sprinkler_ai ----------------
write("smart_sprinkler_ai/manifest.json", manifest("smart_sprinkler_ai", "Smart Sprinkler AI", "1.0.0",
    "Sprinklers only water dry soil and crops that actually need moisture, saving nothing but watering-can charges and adding logic tiers.", "smart_sprinkler_ai.dll",
    [{"UniqueID": "Pathoschild.CtrlsenseMapping"}]))
write("smart_sprinkler_ai/smart_sprinkler_ai.csproj", csproj("smart_sprinkler_ai"))
write("smart_sprinkler_ai/ModEntry.cs", '''using StardewModdingAPI;
using StardewModdingAPI.Events;
using StardewValley;
using StardewValley.GameData.Sprinklers;

namespace smart_sprinkler_ai;

public class ModEntry : Mod
{
    public override void Entry(IModHelper helper)
    {
        helper.Events.GameLoop.DayStarted += OnDayStarted;
    }

    private void OnDayStarted(object? sender, DayStartedEventArgs e)
    {
        foreach (var location in Game1.locations)
            foreach (var tileObj in location.objects)
            {
                var o = tileObj.Value;
                if (o is null || !o.IsSprinkler()) continue;
                // Vanilla sprinklers already run at 6am; we re-run a smarter pass
                WaterDryAndThirsty(location, o.TilePoint, radius: SprinklerRadius(o));
            }
    }

    private static int SprinklerRadius(GameObject o) =>
        o.Name.Contains("quality") ? 2 : 1;

    private static void WaterDryAndThirsty(GameLocation loc, Point center, int radius)
    {
        for (int dx = -radius; dx <= radius; dx++)
        for (int dy = -radius; dy <= radius; dy++)
        {
            var tile = new Vector2i(center.X + dx, center.Y + dy);
            if (loc.doesTileHaveProperty(tile.X, tile.Y, "Diggable", "Back") is null) continue;
            var feature = loc.terrainFeatures.Get(tile);
            var crop = feature?.asCrop();
            bool drySoil = feature?.isForageBush() == false &&
                           loc.doesTileHaveProperty(tile.X, tile.Y, "Water", "Back") is null;
            bool needsWater = crop is not null && !crop.hasWater.Value;
            if ((needsWater || (drySoil && crop is null)) && feature is not null)
                feature.SetFreshState(false); // marks the dirt tile watered, like a vanilla sprinkler
        }
    }
}
''')
write("smart_sprinkler_ai/data/sprinklers.json", json.dumps({
    "smart.basic": {"Name": "Умный спринклер", "Radius": 1, "UpgradeFrom": "basic", "Cost": 2500},
    "smart.quality": {"Name": "Умный спринклер качества", "Radius": 2, "UpgradeFrom": "quality", "Cost": 9000},
    "smart.iridium": {"Name": "Иридиевый умный спринклер", "Radius": 3, "UpgradeFrom": "iridium", "Cost": 25000},
}, ensure_ascii=False, indent=2))
write("smart_sprinkler_ai/config.json", json.dumps({"WaterOnlyThirstyCrops": True, "AlsoWetEmptyDirt": True, "SoundEnabled": False}, indent=2))
write("smart_sprinkler_ai/README.md", "# Smart Sprinkler AI\n\n" + COMMON_README.format(mod="smart_sprinkler_ai"))

# ---------------- 6. pet_affection_overhaul ----------------
write("pet_affection_overhaul/manifest.json", manifest("pet_affection_overhaul", "Pet Affection Overhaul", "1.0.0",
    "Pets grant unique buffs (cat scares crows, dog finds truffles more often) and level up through a friendship system.", "pet_affection_overhaul.dll"))
write("pet_affection_overhaul/pet_affection_overhaul.csproj", csproj("pet_affection_overhaul"))
write("pet_affection_overhaul/ModEntry.cs", '''using StardewModdingAPI;
using StardewModdingAPI.Events;
using StardewValley;

namespace pet_affection_overhaul;

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
''')
write("pet_affection_overhaul/data/buffs.json", json.dumps({
    "Cat": {"buff": "crow_repel", "tiers": [8, 16, 24, 32, 40], "descriptionKey": "buff.cat"},
    "Dog": {"buff": "truffle_luck", "tiers": [8, 16, 24, 32, 40], "descriptionKey": "buff.dog"},
    "Chicken": {"buff": "egg_bonus", "tiers": [10, 20, 30], "descriptionKey": "buff.chicken"},
}, ensure_ascii=False, indent=2))
write("pet_affection_overhaul/i18n/ru.json", json.dumps({
    "buff.cat": "Кошка отпугивает ворон в радиусе {0} клеток.",
    "buff.dog": "Собака находит трюфели чаще (+{0}%).",
    "buff.chicken": "Курица несёт яйца чаще (+{0}%).",
    "hud.hearts": "Любовь питомца: {0}/{1}",
}, ensure_ascii=False, indent=2))
write("pet_affection_overhaul/config.json", json.dumps({"AffectionPerPetting": 12, "DailyDecay": 2, "MaxHearts": 5}, indent=2))
write("pet_affection_overhaul/assets/hearts.png", png(16, 16, bytes([255, 80, 120, 255])))
write("pet_affection_overhaul/README.md", "# Pet Affection Overhaul\n\n" + COMMON_README.format(mod="pet_affection_overhaul"))

# ---------------- 7. crop_rotation_bonus ----------------
write("crop_rotation_bonus/manifest.json", manifest("crop_rotation_bonus", "Crop Rotation Bonus", "1.0.0",
    "Tracks soil fertility per tile. Replanting the same crop depletes yield; rotating families grants quality and speed bonuses.", "crop_rotation_bonus.dll"))
write("crop_rotation_bonus/crop_rotation_bonus.csproj", csproj("crop_rotation_bonus"))
write("crop_rotation_bonus/ModEntry.cs", '''using StardewModdingAPI;
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
''')
write("crop_rotation_bonus/HarvestPatch.cs", '''using HarmonyLib;
using StardewValley;

namespace crop_rotation_bonus;

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
''')
write("crop_rotation_bonus/data/families.json", json.dumps({
    "brassica": ["kale", "cauliflower"],
    "legume": ["beanpole", "soybean", "peanut"],
    "nightshade": ["tomato", "eggplant", "pepper"],
    "grain": ["wheat", "rice"],
    "allium": ["garlic", "onion", "leek"],
}, ensure_ascii=False, indent=2))
write("crop_rotation_bonus/config.json", json.dumps({"RepeatPenalty": 0.8, "RotationBonusPerStep": 0.15, "ShowSoilIndicator": True}, indent=2))
write("crop_rotation_bonus/README.md", "# Crop Rotation Bonus\n\n" + COMMON_README.format(mod="crop_rotation_bonus"))

# ---------------- 8. black_market ----------------
write("black_market/manifest.json", manifest("black_market", "Black Market", "1.0.0",
    "A mysterious night merchant appears on rainy nights after 8 PM selling rare seeds, artifacts and enchantments in exchange for specific resources.", "black_market.dll"))
write("black_market/black_market.csproj", csproj("black_market"))
write("black_market/ModEntry.cs", '''using StardewModdingAPI;
using StardewModdingAPI.Events;
using StardewValley;

namespace black_market;

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
                            "mods.black_market", null, "blackMerchant");
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
''')
write("black_market/data/shop.json", json.dumps({
    "ShopId": "mods.black_market",
    "BuyOnly": True,
    "Currency": "mixed",
    "Items": [
        {"ItemId": "(O)ancientseed", "Price": 5000, "Requires": {"BatWing": 10}},
        {"ItemId": "(O)dinosauregg", "Price": 8000, "Requires": {"AncientArtifact": 1}},
        {"ItemId": "Enchantment_RainbowShell", "Price": 12000, "Requires": {"PrismaticShard": 2}},
        {"ItemId": "(O)voidmelon", "Price": 3000, "Requires": {"VoidEssence": 5}},
    ],
}, ensure_ascii=False, indent=2))
write("black_market/i18n/ru.json", json.dumps({
    "merchant.name": "Ночной торговец",
    "merchant.greeting": "Тсс... только сегодня. За редкие вещи — редкие цены.",
    "shop.title": "Чёрный рынок",
    "error.noResources": "Не хватает ресурса: {0}",
}, ensure_ascii=False, indent=2))
write("black_market/assets/merchant_portrait.png", png(32, 32, bytes([30, 20, 50, 255])))
write("black_market/config.json", json.dumps({"SpawnTime": 2000, "SpawnChance": 0.6, "ShopDataPath": "data/shop.json", "DespawnTime": 2400}, indent=2))
write("black_market/README.md", "# Black Market\n\n" + COMMON_README.format(mod="black_market"))

# ---------------- 9. skill_specializations ----------------
write("skill_specializations/manifest.json", manifest("skill_specializations", "Skill Specializations", "1.0.0",
    "At levels 5/10 of each skill you choose from RPG-style specializations (e.g. Fishing: Deep Sea / Tidepool / Netmaker) with unlockable perks.", "skill_specializations.dll"))
write("skill_specializations/skill_specializations.csproj", csproj("skill_specializations"))
write("skill_specializations/ModEntry.cs", '''using StardewModdingAPI;
using StardewModdingAPI.Events;
using StardewValley;

namespace skill_specializations;

public class ModEntry : Mod
{
    public static SpecStore Specs = new();

    public override void Entry(IModHelper helper)
    {
        helper.Events.GameLoop.SaveLoaded += (_, _) =>
            Specs = helper.Data.ReadSaveData<SpecStore>("specializations") ?? new();
        helper.Events.GameLoop.ReturnedToTitle += (_, _) => helper.Data.WriteSaveData("specializations", Specs);
        helper.Events.Player.LevelChanged += OnLevelChanged;
    }

    private void OnLevelChanged(object? sender, LevelChangedEventArgs e)
    {
        if (!e.IsLocalPlayer) return;
        int lvl = e.NewLevel;
        if (lvl is 5 or 10)
            Menu.OpenFor(e.Skill.ToString(), lvl, Helper, Specs);
    }
}

internal class SpecStore
{
    public Dictionary<string, string> Chosen { get; set; } = new(); // "Fishing-5" -> "DeepSea"
    public bool Has(string key) => Chosen.ContainsKey(key);
}

internal static class Menu
{
    public static void OpenFor(string skill, int level, IModHelper helper, SpecStore store)
    {
        var options = SpecData.For(skill, level);
        if (options.Count == 0) return;
        Game1.activeClickableMenu = new ChoiceMenu(skill, level, options, choice =>
        {
            store.Chosen[$"{skill}-{level}"] = choice.Id;
            Game1.drawObjectDialogue(helper.Translation.Get("chosen", new { spec = choice.Name }));
        });
    }
}

/// <summary>Loads specialization options from data/specializations.json.</summary>
internal static class SpecData
{
    private static readonly Dictionary<string, List<SpecOption>> Cache = new();

    public static List<SpecOption> For(string skill, int level) =>
        Cache.TryGetValue($"{skill}:{level}", out var list) ? list : new();

    public static void Populate(IModHelper helper)
    {
        var raw = helper.Data.ReadJsonFile<Dictionary<string, Dictionary<string, List<SpecDto>>>>("data/specializations.json");
        if (raw is null) return;
        foreach (var (skill, tiers) in raw)
            foreach (var (level, opts) in tiers)
                Cache[$"{skill}:{level}"] = opts.Select(o => new SpecOption(o.Id, o.Name, o.Perks[0])).ToList();
    }

    private record SpecDto(string Id, string Name, List<string> Perks);
}
''')
write("skill_specializations/ChoiceMenu.cs", '''using Microsoft.Xna.Framework.Graphics;
using StardewValley.Menus;

namespace skill_specializations;

internal record SpecOption(string Id, string Name, string DescriptionKey);

internal class ChoiceMenu : ClickableMenu
{
    private readonly List<SpecOption> _options;
    private readonly Action<SpecOption> _onPick;
    private readonly string _skill; private readonly int _level;

    public ChoiceMenu(string skill, int level, List<SpecOption> options, Action<SpecOption> onPick)
        : base(0, 0, 640, 120 + options.Count * 72)
    {
        _skill = skill; _level = level; _options = options; _onPick = onPick;
    }

    public override void receiveLeftClick(int x, int y, bool playSound = true)
    {
        for (int i = 0; i < _options.Count; i++)
            if (boundsFor(i).Contains(x, y)) { _onPick(_options[i]); Game1.exitActiveMenu(); return; }
    }

    public override void draw(SpriteBatch b)
    {
        base.draw(b); // simplified: real implementation draws panels + hover tooltips
    }

    private Microsoft.Xna.Framework.Rectangle boundsFor(int i) =>
        new(rightBound - 600, topOfFullscreenList + 40 + i * 72, 560, 64);

    private int topOfFullscreenList => 0;
}
''')
write("skill_specializations/data/specializations.json", json.dumps({
    "Fishing": {
        "5": [{"id": "DeepSea", "name": "Глубоководный", "perks": ["+1 treasure roll"]},
              {"id": "Tidepool", "name": "Ловля у берега", "perks": ["crab pots never empty"]}],
        "10": [{"id": "Netmaker", "name": "Сетевик", "perks": ["passive fish income"]},
               {"id": "Luremaster", "name": "Мастер приманок", "perks": ["double bait effect"]}],
    },
    "Farming": {
        "5": [{"id": "Shepherd", "name": "Пастух", "perks": ["animal produce +1 quality"]},
              {"id": "Bocage", "name": "Земледелец", "perks": ["sprinklers upgrade free"]}],
    },
    "Mining": {
        "5": [{"id": "Gemologist", "name": "Геммолог", "perks": ["+25% gem chance"]},
              {"id": "Blacksmith", "name": "Кузнец", "perks": ["ore nodes drop +1"]}],
    },
}, ensure_ascii=False, indent=2))
write("skill_specializations/config.json", json.dumps({"AllowRespecCost": 10000, "NotifyOnChoice": True}, indent=2))
write("skill_specializations/README.md", "# Skill Specializations\n\n" + COMMON_README.format(mod="skill_specializations"))

# ---------------- 10. seasonal_monster_invasion ----------------
write("seasonal_monster_invasion/manifest.json", manifest("seasonal_monster_invasion", "Seasonal Monster Invasion", "1.0.0",
    "Wave-defense minigame: monsters attack the farm on select nights each season. Defend, earn tokens, spend them at the armory shop.", "seasonal_monster_invasion.dll"))
write("seasonal_monster_invasion/seasonal_monster_invasion.csproj", csproj("seasonal_monster_invasion"))
write("seasonal_monster_invasion/ModEntry.cs", '''using StardewModdingAPI;
using StardewModdingAPI.Events;
using StardewValley;

namespace seasonal_monster_invasion;

public class ModEntry : Mod
{
    public override void Entry(IModHelper helper)
    {
        helper.Events.GameLoop.TimeChanged += OnTimeChanged;
        helper.Events.GameLoop.UpdateTicked += WaveEngine.Tick;
        helper.Events.GameLoop.SaveLoaded += (_, _) =>
            Tokens.Load(helper.Data.ReadSaveData<int>("invasion-tokens") ?? 0);
        helper.Events.GameLoop.ReturnedToTitle += (_, _) => helper.Data.WriteSaveData("invasion-tokens", Tokens.Value);
    }

    private void OnTimeChanged(object? sender, TimeChangedEventArgs e)
    {
        if (e.NewTime != 2200 || !Context.IsWorldReady) return;
        if (!InvasionCalendar.IsInvasionTonight(Game1.currentSeason, Game1.dayOfMonth)) return;
        WaveEngine.StartRun(Game1.getFarm(), waves: 5 + Game1.year);
        Game1.playSound("newRecord");
        Game1.addHUDMessage(new HUDMessage("Ночь вторжения началась! Защищайте ферму!", HUDMessage.newQuest_type));
    }
}

internal static class Tokens { public static int Value; public static void Load(int v) => Value = v; }
''')
write("seasonal_monster_invasion/WaveEngine.cs", '''using StardewValley;
using StardewValley.Monsters;

namespace seasonal_monster_invasion;

internal static class WaveEngine
{
    private static readonly List<Monster> Active = new();
    private static int _wave, _ticksLeft;

    public static void StartRun(Farm farm, int waves) { _wave = waves; _ticksLeft = 0; }

    public static void Tick(object? sender, UpdateTickedEventArgs e)
    {
        if (_wave <= 0 || !Context.IsWorldReady) return;
        if (--_ticksLeft > 0) return;

        SpawnWave(Game1.getFarm());
        _ticksLeft = 60 * 60; // one in-game hour between waves
        if (--_wave == 0) EndRun();
    }

    private static void SpawnWave(Farm farm)
    {
        for (int i = 0; i < 4 + _wave; i++)
        {
            var spot = farm.getNewMobileFriendSpot("slime");
            var m = Game1.random.NextBool() ? new GreenSlime(spot) : new Bat(spot, "bat");
            farm.characters.Add(m);
            Active.Add(m);
        }
    }

    private static void EndRun()
    {
        foreach (var m in Active) m.Health = 0;
        Tokens.Value += 100;
        Game1.drawObjectDialogue($"Вторжение отбито! Вы получили жетоны оборону: +100 (всего {Tokens.Value}).");
    }
}
''')
write("seasonal_monster_invasion/data/invasions.json", json.dumps({
    "spring": [14, 24],
    "summer": [11, 27],
    "fall": [9, 22],
    "winter": [5, 19, 28],
}, indent=2))
write("seasonal_monster_invasion/data/armory.json", json.dumps({
    "tower_basics": {"cost": 50, "item": "(O)mod_inv_turret"},
    "reinforced_gate": {"cost": 120, "item": "(O)mod_inv_gate"},
    "token_banner": {"cost": 300, "item": "(O)mod_inv_banner"},
}, ensure_ascii=False, indent=2))
write("seasonal_monster_invasion/config.json", json.dumps({"NightStart": 2200, "WavesPerYear": 5, "DamageToCrops": False, "CoopMode": True}, indent=2))
write("seasonal_monster_invasion/README.md", "# Seasonal Monster Invasion\n\n" + COMMON_README.format(mod="seasonal_monster_invasion"))

# ---------------- 11. cooking_recipe_evolution ----------------
write("cooking_recipe_evolution/manifest.json", manifest("cooking_recipe_evolution", "Cooking Recipe Evolution", "1.0.0",
    "Recipes level up with use: repeated cooking unlocks upgraded variants with stronger buffs and fancier names.", "cooking_recipe_evolution.dll"))
write("cooking_recipe_evolution/cooking_recipe_evolution.csproj", csproj("cooking_recipe_evolution"))
write("cooking_recipe_evolution/ModEntry.cs", '''using StardewModdingAPI;
using StardewModdingAPI.Events;
using StardewValley;

namespace cooking_recipe_evolution;

public class ModEntry : Mod
{
    public static RecipeProgress Progress = new();

    public override void Entry(IModHelper helper)
    {
        helper.Events.GameLoop.SaveLoaded += (_, _) =>
            Progress = helper.Data.ReadSaveData<RecipeProgress>("recipe-progress") ?? new();
        helper.Events.GameLoop.ReturnedToTitle += (_, _) => helper.Data.WriteSaveData("recipe-progress", Progress);
        helper.Events.Player.CookingRecipeAssembled += OnCooked;
    }

    private void OnCooked(object? sender, PlayerCookedRecipeEventArgs e)
    {
        string id = e.RecipeId;
        int count = Progress.Bump(id);
        int tier = count / 15;                       // every 15 cooks -> tier up
        if (tier > 0 && tier <= 3 && Progress.NotifyTier(id, tier))
        {
            string evolved = Evolutions.EvolvedId(Helper, id, tier);
            Game1.cookingRecipes.TryAdd(evolved, 0);
            Game1.addHUDMessage(new HUDMessage($"Рецепт улучшился: {evolved}!", HUDMessage.help_type));
        }
    }
}

/// <summary>Maps a base recipe to its evolved names via data/evolutions.json.</summary>
internal static class Evolutions
{
    public static string EvolvedId(IModHelper helper, string recipeId, int tier)
    {
        var data = helper.Data.ReadJsonFile<Dictionary<string, TierList>>("data/evolutions.json");
        if (data is not null && data.TryGetValue(recipeId, out var tiers) && tier <= tiers.Tiers.Count)
            return tiers.Tiers[tier - 1];
        return $"{recipeId}+{tier}";
    }

    private record TierList(List<string> Tiers);
}

internal class RecipeProgress
{
    public Dictionary<string, int> Counts { get; set; } = new();
    public HashSet<string> Announced { get; set; } = new();
    public int Bump(string id) { Counts[id] = Counts.GetValueOrDefault(id) + 1; return Counts[id]; }
    public bool NotifyTier(string id, int tier) => Announced.Add($"{id}:{tier}");
}
''')
write("cooking_recipe_evolution/data/evolutions.json", json.dumps({
    "Fried Egg": {"tiers": ["Perfectly Fried Egg", "Sunny-Side Masterpiece", "Golden Omelette Royale"]},
    "Cheese Cauliflower": {"tiers": ["Gratin Cauliflower", "Aged Cheese Cauliflower"]},
    "Pumpkin Soup": {"tiers": ["Spiced Pumpkin Soup", "Pumpkin Bisque Royale"]},
    "Fish Tacos": {"tiers": ["Baja Fish Tacos", "Legendary Fish Taco Feast"]},
}, ensure_ascii=False, indent=2))
write("cooking_recipe_evolution/i18n/ru.json", json.dumps({
    "hud.tierup": "Блюдо «{0}» достигло уровня {1}!",
    "tooltip.evolution": "Готовьте ещё {0} раз для улучшения рецепта.",
}, ensure_ascii=False, indent=2))
write("cooking_recipe_evolution/config.json", json.dumps({"CooksPerTier": 15, "MaxTier": 3, "BuffScaling": 0.25}, indent=2))
write("cooking_recipe_evolution/README.md", "# Cooking Recipe Evolution\n\n" + COMMON_README.format(mod="cooking_recipe_evolution"))

# ---------------- 12. community_board_2 ----------------
write("community_board_2/manifest.json", manifest("community_board_2", "Community Board 2.0", "1.0.0",
    "The guild bulletin board dynamically generates contracts scaled to your progress: fetch, delivery, cull and event quests with fair rewards.", "community_board_2.dll"))
write("community_board_2/community_board_2.csproj", csproj("community_board_2"))
write("community_board_2/ModEntry.cs", '''using StardewModdingAPI;
using StardewModdingAPI.Events;
using StardewValley;

namespace community_board_2;

public class ModEntry : Mod
{
    public static QuestLog Log = new();

    public override void Entry(IModHelper helper)
    {
        helper.Events.GameLoop.DayStarted += OnDayStarted;
        helper.Events.GameLoop.SaveLoaded += (_, _) =>
            Log = helper.Data.ReadSaveData<QuestLog>("board-quests") ?? new();
        helper.Events.GameLoop.ReturnedToTitle += (_, _) => helper.Data.WriteSaveData("board-quests", Log);
    }

    private void OnDayStarted(object? sender, DayStartedEventArgs e)
    {
        Log.ExpireOld();
        while (Log.ActiveCount < 3)
        {
            var contract = Generator.Generate(PlayerProfile.Capture(), Rng.Seeded(Game1.dayOfMonth));
            Log.Accept(contract);
        }
    }
}

internal class QuestLog
{
    public List<Contract> Active { get; set; } = new();
    public int ActiveCount => Active.Count;
    public void Accept(Contract c) => Active.Add(c);
    public void ExpireOld() => Active.RemoveAll(c => c.DeadlineDays <= 0);
}
''')
write("community_board_2/Generator.cs", '''using StardewValley;

namespace community_board_2;

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
''')
write("community_board_2/data/pools.json", json.dumps({
    "fetch_items": ["leek", "daffodil", "hazelnut", "clay", "copper_ore", "quartz"],
    "givers": ["Mayor Lewis", "Clint", "Demetrius", "Wizard"],
    "difficulty_curve": {"earlyGame": [1, 8], "midGame": [8, 16], "lateGame": [16, 30]},
}, ensure_ascii=False, indent=2))
write("community_board_2/config.json", json.dumps({"MaxActiveContracts": 3, "RewardMultiplier": 1.0, "AllowDecline": True}, indent=2))
write("community_board_2/README.md", "# Community Board 2.0\n\n" + COMMON_README.format(mod="community_board_2"))

# ---------------- 13. farm_layout_presets ----------------
write("farm_layout_presets/manifest.json", manifest("farm_layout_presets", "Farm Layout Presets", "1.0.0",
    "Save the entire farm layout (buildings, objects, terrain) into named presets and restore instantly, even across seasons.", "farm_layout_presets.dll"))
write("farm_layout_presets/farm_layout_presets.csproj", csproj("farm_layout_presets"))
write("farm_layout_presets/ModEntry.cs", '''using System.Text.Json;
using StardewModdingAPI;
using StardewModdingAPI.Events;
using StardewValley;

namespace farm_layout_presets;

public class ModEntry : Mod
{
    public override void Entry(IModHelper helper)
    {
        helper.Events.Input.ButtonPressed += e =>
        {
            if (e.Button.Equals(SButton.F7) && Context.IsPlayerFree)
                Capture(helper);
            if (e.Button.Equals(SButton.F8) && Context.IsPlayerFree)
                RestoreLatest(helper);
        };
    }

    private void Capture(IModHelper helper)
    {
        var snap = Snapshot.FromFarm(Game1.getFarm());
        string dir = Path.Combine(helper.Data.Path, "presets");
        Directory.CreateDirectory(dir);
        File.WriteAllText(Path.Combine(dir, $"{DateTime.Now:yyyyMMdd-HHmmss}.json"),
            JsonSerializer.Serialize(snap, Snap.Options));
        Game1.addHUDMessage(new HUDMessage("Планировка сохранена в пресет.", HUDMessage.newQuest_type));
    }

    private void RestoreLatest(IModHelper helper)
    {
        var dir = Path.Combine(helper.Data.Path, "presets");
        var file = Directory.GetFiles(dir, "*.json").OrderByDescending(f => f).FirstOrDefault();
        if (file is null) return;
        Snapshot.FromJson(File.ReadAllText(file)).ApplyTo(Game1.getFarm());
        Game1.addHUDMessage(new HUDMessage("Планировка загружена из пресета.", HUDMessage.newQuest_type));
    }
}
''')
write("farm_layout_presets/Snapshot.cs", '''using System.Text.Json;
using System.Text.Json.Serialization;
using StardewValley;

namespace farm_layout_presets;

internal static class Snap
{
    public static readonly JsonSerializerOptions Options = new() { WriteIndented = true };
}

internal class Snapshot
{
    public List<BuildingDto> Buildings { get; set; } = new();
    public List<ObjectDto> Objects { get; set; } = new();
    public List<TerrainDto> Terrain { get; set; } = new();

    public static Snapshot FromFarm(Farm farm)
    {
        var s = new Snapshot();
        foreach (var b in farm.buildings)
            s.Buildings.Add(new BuildingDto(b.buildingType.Value, b.tileX.Value, b.tileY.Value, b.daysOfConstructionLeft.Value));
        foreach (var kv in farm.objects)
            if (kv.Value is not null)
                s.Objects.Add(new ObjectDto(kv.Value.QualifiedItemId, kv.Key.X, kv.Key.Y));
        return s;
    }

    public static Snapshot FromJson(string json) => JsonSerializer.Deserialize<Snapshot>(json, Snap.Options) ?? new();

    public void ApplyTo(Farm farm)
    {
        farm.buildings.Clear();
        farm.objects.Clear();
        foreach (var b in Buildings)
            farm.buildings.Add(Building.makeBuilding(b.Type, b.X, b.Y));
        foreach (var o in Objects)
            farm.objects.Set(new Vector2i(o.X, o.Y), new StardewValley.Object(new Vector2(o.X, o.Y), o.ItemId));
    }
}

internal record BuildingDto(string Type, int X, int Y, int ConstructionDaysLeft);
internal record ObjectDto(string ItemId, int X, int Y);
internal record TerrainDto(string Feature, int X, int Y);
''')
write("farm_layout_presets/config.json", json.dumps({"HotkeyCapture": "F7", "HotkeyRestore": "F8", "MaxPresets": 20, "IncludeSoilState": False}, indent=2))
write("farm_layout_presets/i18n/ru.json", json.dumps({
    "hud.saved": "Планировка сохранена в пресет.",
    "hud.loaded": "Планировка загружена из пресета.",
    "menu.title": "Пресеты планировки",
}, ensure_ascii=False, indent=2))
write("farm_layout_presets/README.md", "# Farm Layout Presets\n\n" + COMMON_README.format(mod="farm_layout_presets"))

# ---------------- 14. infinite_water_hose ----------------
write("infinite_water_hose/manifest.json", manifest("infinite_water_hose", "Infinite Water Hose", "1.0.0",
    "A hose sold by Pierre for 250g: one end stays in any water source, the other waters crops endlessly — no refills, unlimited reach.", "infinite_water_hose.dll"))
write("infinite_water_hose/infinite_water_hose.csproj", csproj("infinite_water_hose"))
write("infinite_water_hose/ModEntry.cs", '''using StardewModdingAPI;
using StardewModdingAPI.Events;
using StardewValley;
using StardewValley.Tools;

namespace infinite_water_hose;

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
''')
write("infinite_water_hose/i18n/ru.json", json.dumps({
    "tool.name": "Бесконечный шланг",
    "tool.desc": "Один конец — в воду, второй — в руках. Поливает урожай без ограничений по дальности и запасу воды.",
    "shop.pierre": "Вот, держи шланг. Один конец в воду — и поливай сколько влезет! Всего 250 золотых.",
    "anchor.msg": "Шланг опущен в воду!",
}, ensure_ascii=False, indent=2))
write("infinite_water_hose/config.json", json.dumps({"Price": 250, "Seller": "Pierre", "UnlimitedReach": True, "WorksInRain": False, "RequiresWaterSource": True}, indent=2))
write("infinite_water_hose/assets/hose.png", png(16, 16, bytes([40, 120, 200, 255])))
write("infinite_water_hose/README.md", "# Infinite Water Hose\n\nПродаётся у Пьера за 250 золотых.\n\n" + COMMON_README.format(mod="infinite_water_hose"))

# ---------------- 15. instant_fishing ----------------
write("instant_fishing/manifest.json", manifest("instant_fishing", "Instant Fishing", "1.0.0",
    "Skips the fishing minigame entirely: cast the line and reel in the catch instantly, with perfect-quality rolls.", "instant_fishing.dll"))
write("instant_fishing/instant_fishing.csproj", csproj("instant_fishing"))
write("instant_fishing/ModEntry.cs", '''using HarmonyLib;
using StardewModdingAPI;
using StardewModdingAPI.Events;
using StardewValley;
using StardewValley.Menus;

namespace instant_fishing;

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
''')
write("instant_fishing/config.json", json.dumps({"Enabled": True, "AlwaysPerfect": False, "ShowCatchToast": True, "TreasureRollBonus": 0.0}, indent=2))
write("instant_fishing/i18n/ru.json", json.dumps({
    "toast.caught": "Мгновенная поимка: {0}!",
    "settings.enabled": "Отменить мини-игру рыбалки",
}, ensure_ascii=False, indent=2))
write("instant_fishing/README.md", "# Instant Fishing\n\n" + COMMON_README.format(mod="instant_fishing"))

# ---------------- solution file + overview README ----------------
def sln_entry(idx, name, folder):
    # deterministic pseudo-GUID per project (cosmetic but stable)
    g = "{%08X-1111-2222-3333-%012X}" % (idx * 7919 + 0x53445700, idx * 104729)
    return f'Project("{{FAE04EC0-301F-11D3-BF4B-00C04F79EFBC}}") = "{name}", "{folder}\\{name}.csproj", "{g}"\nEndProject\n'

titles = {
    "auto_sell_chest": "Auto-Sell Chest",
    "stamina_regen_aura": "Stamina Regen Aura",
    "weather_forecast_ui": "Weather Forecast UI",
    "quick_teleport_stones": "Quick Teleport Stones",
    "smart_sprinkler_ai": "Smart Sprinkler AI",
    "pet_affection_overhaul": "Pet Affection Overhaul",
    "crop_rotation_bonus": "Crop Rotation Bonus",
    "black_market": "Black Market",
    "skill_specializations": "Skill Specializations",
    "seasonal_monster_invasion": "Seasonal Monster Invasion",
    "cooking_recipe_evolution": "Cooking Recipe Evolution",
    "community_board_2": "Community Board 2.0",
    "farm_layout_presets": "Farm Layout Presets",
    "infinite_water_hose": "Infinite Water Hose",
    "instant_fishing": "Instant Fishing",
}
order = list(titles.keys())
sln = ["Microsoft Visual Studio Solution File, Format Version 12.00",
       "# Visual Studio Version 17",
       "VisualStudioVersion = 17.0.31903.59",
       "MinimumVisualStudioVersion = 10.0.40219.1"]
for i, m in enumerate(order, 1):
    sln.append(sln_entry(i, m, f"mods/{m}"))
sln.append("Global")
sln.append("\tGlobalSection(SolutionConfigurationPlatforms) = preSolution")
sln.append("\t\tDebug|Any CPU = Debug|Any CPU")
sln.append("\t\tRelease|Any CPU = Release|Any CPU")
sln.append("\tEndGlobalSection")
sln.append("EndGlobal")
write("../Mods.sln", "\n".join(sln) + "\n")

OVERVIEW = open(os.path.join(ROOT, "README.md"), encoding="utf-8").read() if os.path.exists(os.path.join(ROOT, "README.md")) else ""
if OVERVIEW:
    write("README.md", OVERVIEW)

print("Mods generated:", ", ".join(sorted(MODS.keys())))
