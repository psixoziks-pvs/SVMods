using StardewModdingAPI;
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
