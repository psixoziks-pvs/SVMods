using System.Text.Json;
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
