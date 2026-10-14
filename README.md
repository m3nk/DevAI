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
   (or add a new entry with `title`, `icon`, `desc`, `file`, `status`).
3. Done — the dashboard picks it up automatically.

No server required; everything runs from `file://` or any static host (GitHub Pages works).
