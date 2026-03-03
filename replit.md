# Eldoria Quest — Discord Bot

## Overview
A dark high-fantasy survival RPG Discord bot. Players explore dungeons, gather materials, fight monsters, and grow their characters in real-time asynchronous expeditions.

Inspired by: *Danmachi* (guild hierarchy, dungeon progression) and *Grimgar of Fantasy and Ash* (material-driven survival).

## Tech Stack
- **Language:** Python 3.12
- **Discord Library:** discord.py 2.6.4 (slash commands, Views, Modals)
- **Database:** MongoDB via pymongo 4.16.0
- **Environment:** python-dotenv for secrets management
- **HTTP:** aiohttp (health check server for deployment)

## Required Secrets
- `DISCORD_BOT_TOKEN` — Discord bot token from the Developer Portal
- `MONGO_URI` — MongoDB connection string (e.g., MongoDB Atlas)

## Project Structure
```
main.py               # Entry point — bot init, cog loading, DB init
cogs/                 # Discord command modules (20 cogs)
  adventure_cog.py    # Expedition commands
  shop_cog.py         # Item shop
  character_cog.py    # Character management
  tournament_cog.py   # Weekly tournaments
  ... (and more)
game_systems/         # Core game engine logic
  adventure/          # Expedition and event handling
  combat/             # Damage formulas, auto-combat
  data/               # Static game data (JSON + Python dicts)
  player/             # Stats, leveling, achievements
  guild_system/       # Factions, ranks, tournament system
database/             # DB abstraction layer
  database_manager.py # MongoDB operations
  create_database.py  # Collection/index creation
  populate_database.py# Seed data population
scripts/              # Utility and build scripts
tests/                # Pytest test suite
docs/                 # Design and planning documents
logs/                 # Runtime logs (auto-created)
```

## Workflow
- **Start application** — runs `python main.py` as a console workflow
- The bot also starts an aiohttp health check server on port 10000

## Architecture Notes
- Cogs are dynamically loaded from the `cogs/` directory on startup
- MongoDB collections are created/indexed on startup via `create_tables()`
- Game data is seeded via `populate_database.py` (idempotent upserts)
- The bot uses global slash command sync (may take up to 1 hour to propagate)
- Health check server runs on `PORT` env var (default 10000) for deployment platforms

## Known Fixes Applied
- Fixed `tournament_system.py`: `type=` → `tournament_type=` keyword argument to match `DatabaseManager.create_tournament()` signature
