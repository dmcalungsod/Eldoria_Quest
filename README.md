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

Civilization survives only within fortified enclaves like **Astraeon**, the capital city where the **Adventurer’s Guild** operates. Adventurers fight not for glory, but survival.

The game blends:

- **Guild-Driven Progression** (Danmachi-Style)
- **Material-Based Economy & Harsh Survival** (Grimgar-Style)
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
- Combat plays out automatically with suspenseful **1.5-second turn delays**.
- Narration is both **class-aware** (Mages cast spells, Warriors cleave) and **monster-aware**.
- Player **HP/MP persists** between actions and must be healed manually or by resting.

---

# 🜂 Core Gameplay Loop

1.  **Register** — Use `/start` to create your character, choose a class, and receive your **Guild Card**.
2.  **Explore** — From the profile UI, choose a location and press **"Explore"**.
3.  **Survive** — Each press of "Explore" triggers one of two events:
    - **Combat (60%):** You encounter a monster. The battle plays out automatically, with your character using skills and attacks via an "Auto-Skill AI".
    - **Rest (40%):** You find nothing, "catch your breath," and regenerate a small amount of HP and MP based on your stats.
4.  **Manage** — During the adventure, you can press **"Inventory"** to pause and use a potion or equip a newly looted item.
5.  **Return** — Click **"Return to City"** to end your adventure. This banks your EXP and fully restores your HP and MP. If you die, you are forcibly returned with 1 HP.
6.  **Progress** — Back at the **Guild Hall**, you can sell materials at the **Guild Exchange**, turn in quests, and request promotion to the next Guild Rank (F → SSS).

---

# 🧩 Major Features

- Persistent **"ONE UI" System** (No slash commands needed after `/start`)
- **Manual Exploration** (button-driven, not timed)
- **Turn-by-Turn Combat Playback** (1.5s delay for suspense)
- **Auto-Skill Combat AI** (Mages cast spells, Clerics heal, Warriors strike)
- **"Explore-to-Regen"** HP/MP System
- **Loot-Only Economy** (Materials must be sold at the Guild)
- **Full Equipment System** (Equip/Unequip from inventory, stats auto-recalculate)
- **Full Consumable System** (Use potions to heal persistent HP)
- **Persistent Player Vitals** (HP/MP are saved to the database)
- **Detailed Guild Rank System** (F to SSS) with promotion checks
- **Quest System** with automatic "defeat" and "collect" objective tracking

---

# 🗂️ Project Structure

```

eldoria-bot/
├─ main.py \# Bot entry point
├─ README.md
├─ requirements.txt
│
├─ cogs/
│ ├─ onboarding_cog.py \# /start, character creation
│ ├─ character_cog.py \# Profile, Inventory, Skills UI
│ ├─ guild_hub_cog.py \# Guild Hall, Rank Up, Exchange UI
│ ├─ quest_hub_cog.py \# Quest Board and Quest Log UI
│ ├─ adventure_commands.py \# The main "Explore" adventure UI
│ └─ ui_helpers.py \# Shared navigation functions (back_to_profile...)
│
├─ database/
│ ├─ database_manager.py \# DB interface (CRUD operations)
│ ├─ create_database.py \# The master schema
│ └─ populate_database.py \# Fills DB with items, monsters, quests
│
├─ game_systems/
├─ adventure/
│ ├─ adventure_manager.py
│ └─ adventure_session.py
├─ combat/
│ ├─ combat_engine.py
│ ├─ combat_phrases.py
│ └─ damage_formula.py
├─ data/
│ ├─ class_data.py
│ ├─ monsters.py
│ ├─ materials.py
│ ├─ consumables.py
│ ├─ skills_data.py
│ └─ ... (etc)
├─ guild_system/
│ ├─ guild_exchange.py
│ ├─ quest_system.py
│ ├─ rank_system.py
│ └─ reward_system.py
├─ items/
│ ├─ item_manager.py
│ ├─ inventory_manager.py
│ ├─ equipment_manager.py
│ └─ consumable_manager.py
├─ monsters/
│ └─ monster_actions.py
├─ player/
├─ player_creator.py
├─ player_stats.py
└─ level_up.py

```

---

# 🛡️ License & Ownership

This repository is **private intellectual property**. All source code, lore, mechanics, and documentation belong solely to the project owner.

**Not open-source. Not licensed for redistribution or reuse.**
