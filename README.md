# DevAI Arcade

A growing collection of self-contained HTML5 games with a simple dashboard launcher.

## Structure

```
index.html      ← the dashboard (open in any browser)
games/          ← one HTML file per game, no build step, no dependencies
```

## Adding a game

1. Drop the game as a single HTML file into `games/` (e.g. `games/snake.html`).
2. In `index.html`, find the `GAMES` registry and set that game's `status` to `"play"`
   (or add a new entry with `title`, `icon`, `desc`, `file`, `type`, `status`).
3. Add the **🕹️ Menu** pill (returns to the dashboard) to the new game: list it in the
   `CFG` table of `tools/inject_dashboard_menu.py` — pick the corner whose HUD is free
   (`corner: "tl"|"tr"|"bl"|"br"`, or `hud: <fraction of canvas height>` /
   `fit: (LW, LH, y)` when the game paints its HUD on the canvas) — then run
   `python3 tools/inject_dashboard_menu.py`. It is idempotent and only ever adds a block
   between `<!-- DEVAI-MENU:BEGIN -->` / `END`.
4. Done — the dashboard picks the game up automatically.

No server required; everything runs from `file://` or any static host (GitHub Pages works).
