# Board Game Analyzer

**Real-time strategy analysis for board games on [Board Game Arena](https://boardgamearena.com) (and any game you can play online eventually)**

---

## Why We Built This

If you've ever sat around a table (or a screen) playing board games with your friends and thought *"Was that actually a good move?"* — that's exactly where this project started.
Our group plays a lot of board games together. We love the strategy, we love the competition, and we love the post-game arguments about who made the biggest blunder. But here's the thing: for most board games, there's almost no strategy content out there. Chess has engines, opening books, and thousands of YouTube breakdowns. Go has AI analysis tools. But if you're playing Connect Four on a weird 8x9 board, or working through a game of Civilization: A New Dawn, you're pretty much on your own.
We wanted to understand **how individual plays actually affect the outcome of a game** — not just gut feelings, but real positional evaluation that tracks momentum shift by shift, move by move. The kind of thing that lets you look back at a game and say *"This is the exact moment things turned around."*
So we started building a real-time strategy engine. The long-term goal is to use it to create **strategy guides backed by actual analysis** — showing what's proven to work, what the critical decision points are, and what separates a strong play from a weak one, for games that have never had that kind of breakdown before.
That's what this is. It's early. It's a passion project. And we're having a lot of fun with it.

---

## What It Does

Board Game Analyzer is a Chrome extension that connects to [Board Game Arena](https://boardgamearena.com) and provides **live analysis while you play**. Here's what it looks like in practice:

- **Momentum Tracking** — A tug-of-war style meter that shows which player has the advantage and how it shifts with every move
- **Win Probability** — Real-time estimated win percentage for each player
- **Move Quality Rating** — Each move gets graded so you can see whether you're making strong or weak plays
- **Player Accuracy** — Tracks how well each player is playing overall throughout the game
- **Game Timeline** — A visual history of the entire game that you can scrub through to see how the advantage evolved over time
- **Move History** — Detailed log of every move with evaluation scores

The extension injects a sidebar directly into the BGA game page, so everything happens in real time without switching tabs or windows.

### How It Works (Under the Hood)

The system has three main pieces:

1. **Chrome Extension** — Detects what game you're playing on BGA, reads the game state from the page, and displays the analysis sidebar
2. **Backend Engine** — A FastAPI server that receives board states over WebSocket, runs them through game-specific evaluation engines, and returns analysis results with momentum calculations
3. **Game Engines** — Each supported game has its own evaluator that understands the rules, strategy, and positional factors specific to that game

---

## What It Doesn't Do (Yet)

Let's be upfront about where things stand:

- **It doesn't play for you** — This isn't a bot or an auto-player. It's an analysis tool that helps you understand the game better
- **It won't tell you the perfect move** — For complex games, it evaluates the current position and momentum rather than searching every possible future move
- **It's not finished** — The UI is evolving, the engines are getting smarter, and we're actively adding games
- **BGA only (for now)** — Currently it only works with Board Game Arena, though the engine architecture is designed to be platform-flexible

---

## Supported Games

| Game | Status | Notes |
|------|--------|-------|
| **Connect Four** | Live | Full positional evaluation with variable board sizes (including BGA's 8x9 variant) |
| **Civilization: A New Dawn** | Live | Deep evaluation covering territory, military, economy, tech, diplomacy, wonders, focus row, victory progress, districts, resources, forts, and strategic positioning. Supports the Terra Incognita expansion |

Yeah, it's a short list right now. But each game gets a proper, thoughtful engine — not a generic one-size-fits-all approach. We'd rather do two games well than twenty games badly.

---

## Our Timeline

Honestly? There's no rush. This is a side project that we work on when we're excited about it, which happens to be pretty often. We don't have a release schedule or a roadmap with deadlines. We'll keep adding games, improving the engines, and polishing the UI at whatever pace feels right.

If you're wondering when your favorite game might get added — the answer is probably "eventually, or sooner if you ask nicely." (See below.)

---

## Tech Stack

- **Backend:** Python, FastAPI, WebSocket, SQLAlchemy
- **Game Engines:** Custom per-game evaluators with momentum and position scoring
- **Extension:** TypeScript, Chrome Manifest V3, Vite
- **Frontend:** TypeScript sidebar with live-updating visualizations
- **Deployment:** Docker, Nginx reverse proxy

---

## Getting Started

### Prerequisites

- Google Chrome browser
- A [Board Game Arena](https://boardgamearena.com) account
- Node.js 18+ (for building the extension)

### Building the Extension

```bash
cd extension
npm install
npm run build
```

Then load it in Chrome:

1. Go to `chrome://extensions/`
2. Enable "Developer mode" (top right toggle)
3. Click "Load unpacked"
4. Select the `extension/dist` folder

### Running the Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Or with Docker:

```bash
docker-compose up
```

---

## Want Us to Add Your Favorite Game?

This is the part where we genuinely mean it: **we want to hear from you.**

If there's a board game you love that you wish had better strategy analysis, open an issue and tell us about it. We're especially interested in:

- Games you play regularly on Board Game Arena
- Games where you feel like there's a gap in strategy content
- Games where you'd love to see move-by-move analysis

We can't promise we'll get to everything, but we *can* promise we'll read every suggestion. The games we've built so far came from our own game nights, but some of the best ideas come from people who are passionate about games we haven't even tried yet.

**[Open an issue](https://github.com/oppitheshort/board-game-analyzer/issues/new) and tell us what you want to see.**

You can also suggest improvements to existing game engines, UI features, or anything else. We're building this in the open because we think the board gaming community deserves better strategy tools, and the best way to build something useful is to listen to the people who'll actually use it.

---

## Contributing

Want to help build an engine for a game you know inside and out? We'd love that. Each game engine is self-contained in `backend/app/engine/`, and the extension's game extractors live in `extension/content/games/`. If you understand a game's strategy deeply and want to take a crack at writing an evaluator, reach out or submit a PR.

---

## License

This project is open source. Have fun with it.

---

*Built by a group of friends who got tired of arguing about whether that was actually a good move.*
