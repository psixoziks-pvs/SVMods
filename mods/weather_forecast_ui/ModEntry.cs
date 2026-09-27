using StardewModdingAPI;
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
