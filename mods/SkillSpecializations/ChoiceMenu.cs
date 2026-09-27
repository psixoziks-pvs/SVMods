using Microsoft.Xna.Framework.Graphics;
using StardewValley.Menus;

namespace SkillSpecializations;

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
