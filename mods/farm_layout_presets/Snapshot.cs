using System.Text.Json;
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
