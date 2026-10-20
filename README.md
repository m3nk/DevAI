# DevAI Arcade

A growing collection of self-contained HTML5 games with a simple dashboard launcher.

> **AI-built:** all content in this repository — including every game — is built using
> AI: **Qwen 3.8 Flash Next**.

## Structure

```
index.html      ← the dashboard (open in any browser)
games/          ← one HTML file per game, no build step, no dependencies
```

## Adding a game

1. Drop the game as a single HTML file into `games/` (e.g. `games/snake.html`).
2. In `index.html`, find the `GAMES` registry and set that game's `status` to `"play"`
   (or add a new entry with `title`, `icon`, `desc`, `file`, `type`, `status`).
3. Add the shared **in-game chrome** — the `🕹️ Menu` pill (back to the dashboard) and the
   `🗑 Clear` button (wipes that game's saved data) — by adding the game to the `CFG`
   table of `tools/inject_dashboard_menu.py`, then running
   `python3 tools/inject_dashboard_menu.py`. It is idempotent and byte-stable: it only
   ever rewrites the block between `<!-- DEVAI-MENU:BEGIN -->` / `END`.
   - `corner: "tl"|"tr"|"bl"|"br"` picks the corner whose HUD is free. When a game paints
     its HUD on the canvas, use `hud: <fraction of canvas height>` or
     `fit: (LW, LH, y)` (for a letterboxed `contain`-fit canvas) so the row parks just
     below that band instead of over it.
   - `keys` / `pref` are that game's own `localStorage` key names / prefixes. The Clear
     button deletes **only** those, so no game can wipe another's records; a prefix that
     could match another game's key makes the script refuse to run.
4. Done — the dashboard picks the game up automatically.

## Saved data

Scores and settings are kept in `localStorage`, per game and per browser. The `🗑 Clear`
button in every game deletes that game's own keys and reloads — it asks first
(`⚠ Sure?`, two clicks), and never touches another game's data. A game that stores
nothing reports `∅ Nothing saved`.

No server required; everything runs from `file://` or any static host (GitHub Pages works).
