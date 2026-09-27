using StardewModdingAPI;
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
