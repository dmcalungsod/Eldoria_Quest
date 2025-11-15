# 🌑 **Eldoria Quest**

### _A Dark High-Fantasy Idle RPG Discord Bot_

Inspired by:

- **Danmachi** — guild ranks, dungeon progression, structured growth
- **Grimgar of Fantasy and Ash** — grounded survival, emotional weight, realism
- **Classic literary fantasy** — atmospheric, book-like narration

---

<p align="center">
  <img src="https://img.shields.io/badge/status-private%20project-darkred?style=for-the-badge"/>
  <img src="https://img.shields.io/badge/built_for-personal%20use-blue?style=for-the-badge"/>
  <img src="https://img.shields.io/badge/not_open_source-grey?style=for-the-badge"/>
</p>

---

# 🜁 **World & Theme**

**Eldoria Quest** is a private, personal RPG system set in a fractured world reshaped by **The Sundering**—a magical catastrophe that shattered the Veil and unleashed horrors across the realm.

Civilization survives only within fortified enclaves like **Astraeon**, the capital city where the **Eldorian Adventurer’s Consortium** operates. Adventurers fight not for glory, but survival.

The game blends:

- **Guild-Driven Progression** (Danmachi)
- **Material-Based Economy & Harsh Survival** (Grimgar)
- **Literary, atmospheric narration** for every action

---

# ⭐ Design Philosophy

### 🜄 Loot-Driven Economy (Danmachi-Style)

- Monsters do **not** drop coins.
- They drop **Magic Stones** and **Monster Materials** (fangs, claws, hides).
- All currency (**Aurum**) comes from selling materials at the **Guild Exchange**.
- Every adventure becomes a calculated risk for better loot.

### 🜃 Immersive UI & Narrative (Grimgar-Style)

- A single persistent **“ONE UI”** message — minimal slash commands.
- Combat plays out automatically with suspenseful timed narration.
- Narration is both **class-aware** and **monster-aware**.
- Player HP/MP persists until healed.

---

# 🜂 Core Gameplay Loop

1. **Register** — Use `/start` to create your character and receive your **Guild Card**.
2. **Explore** — From the profile UI, choose a location and press **Explore**.
3. **Survive** — Each exploration triggers combat, rest, or a story event; combat logs post every 5 minutes.
4. **Manage** — Use Inventory to equip gear or consume potions during or after runs.
5. **Return** — End the adventure to receive EXP and materials; heal and rest at the Guild Hall.
6. **Progress** — Sell materials at the **Guild Exchange** for Aurum, turn in quests, and rank up (F → SSS).

---

# 🧩 Major Features

- Persistent **ONE UI** system (no constant slash commands)
- Idle adventure simulation with 5-minute log cadence
- Auto-skill combat AI and class/monster-aware narration
- Loot-only economy; materials sold at Guild Exchange for Aurum
- Full equipment & consumable systems with persistent HP/MP
- Quest system with automatic objective tracking
- Rank progression (F → SSS) and Guild Merit mechanics

---

# 🗂️ Project Structure

```

eldoria-bot/
├─ main.py # Bot entry point
├─ config.py # Global configuration / constants
├─ README.md
├─ requirements.txt
│
├─ cogs/
│ ├─ onboarding_cog.py # /start, character creation
│ ├─ character_cog.py # Profile, Inventory, Skills UI
│ ├─ guild_hub_cog.py # Guild Hall, Rank Up, Exchange UI
│ ├─ quest_hub_cog.py # Quest Board, Quest Log UI
│ ├─ adventure_commands.py # Explore, adventure session UI
│ └─ ui_helpers.py # Shared navigation utilities (no cross-cog imports)
│
├─ ui/
│ ├─ guild_card_view.py # Views/buttons for main player card
│ ├─ quest_board_view.py # Quest board dropdowns & pages
│ ├─ quest_log_view.py # Quest progress views
│ └─ navigation.py # back_to_guild_card callbacks (safe imports)
│
├─ database/
│ ├─ database_manager.py # DB interface
│ ├─ create_database.py # Schema creation script
│ └─ populate_database.py # Seed data insertion
│
├─ game_systems/
│ ├─ adventure/
│ │ ├─ adventure_manager.py
│ │ └─ adventure_session.py
│ ├─ combat/
│ │ ├─ combat_engine.py
│ │ ├─ combat_phrases.py
│ │ └─ damage_formula.py
│ ├─ data/
│ │ ├─ class_data.py
│ │ ├─ monster_data.py
│ │ ├─ materials.py
│ │ ├─ consumables.py
│ │ └─ skills_data.py
│ └─ guild_system/
│ ├─ guild_exchange.py
│ ├─ quest_system.py
│ ├─ rank_system.py
│ └─ reward_system.py
│
├─ items/
│ ├─ item_manager.py
│ ├─ inventory_manager.py
│ ├─ equipment_manager.py
│ └─ consumable_manager.py
│
└─ player/
├─ player_creator.py
├─ player_stats.py
└─ level_up.py

```

> **Notes:**
>
> - `cogs/` modules **must not** import each other. They only import from `ui/`, `game_systems/`, and `database/`.
> - Keep UI code in `ui/` to avoid circular imports. Import views lazily in callbacks if needed.
> - Business logic lives under `game_systems/` and never imports from `cogs/` or `ui/`.

---

# 🛡️ License & Ownership

This repository is **private intellectual property**. All source code, lore, mechanics, and documentation belong solely to the project owner.

**Not open-source. Not licensed for redistribution or reuse.**

```

```
