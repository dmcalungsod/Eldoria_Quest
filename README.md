# 🌑 **Eldoria Quest**

### _A Dark High-Fantasy Survival RPG Discord Bot_

Inspired by:

- **Danmachi** — guild ranks, dungeon structure, steady progression
- **Grimgar of Fantasy and Ash** — grounded danger, fragile mortality, material-driven survival
- **Literary fantasy** — atmospheric narration, immersive tone, worldbuilding through text

---

\<p align="center"\>
  \<img src="[https://img.shields.io/badge/status-private%20project-darkred?style=for-the-badge](https://img.shields.io/badge/status-private%20project-darkred?style=for-the-badge)"/\>
  \<img src="[https://img.shields.io/badge/built_for-personal%20use-blue?style=for-the-badge](https://img.shields.io/badge/built_for-personal%20use-blue?style=for-the-badge)"/\>
  \<img src="[https://img.shields.io/badge/not_open_source-grey?style=for-the-badge](https://img.shields.io/badge/not_open_source-grey?style=for-the-badge)"/\>
\</p\>

---

# 🜁 **World & Theme**

**Eldoria Quest** unfolds in a world shattered by **The Sundering**, a cataclysm that tore apart the Veil and unleashed horrors across the realm.

Civilization survives only inside fortified enclaves such as **Astraeon**, home of the **Adventurer’s Guild**—an institution born from necessity rather than prestige. Adventurers are not heroes; they are workers who risk their lives so the city may endure.

Your character serves the Guild with the official occupation of **Adventurer**, tasked with reclaiming the wilds one dangerous step at a time.

The game blends:

- **Guild-driven structure** (Danmachi)
- **Material-based survival realism** (Grimgar)
- **Literary, atmospheric narration** across all actions

---

# ⭐ **Design Philosophy**

### 🜄 Material-Driven Survival (Danmachi-Style Economics)

- Monsters drop **Magic Stones** and **Monster Materials**, not currency.
- All Aurum is earned by selling materials at the **Guild Exchange**.
- Every expedition is a calculated risk with uncertain profit.

### 🜃 Story-Focused Immersion (Grimgar-Style)

- Almost the entire game runs through a single persistent **ONE UI** message.
- Exploration is **manual**, turn-based, and intentionally slow-paced.
- Every action is narrated with book-like atmosphere and class awareness.
- HP/MP persist between actions — healing is precious.

---

# 🜂 **Core Gameplay Loop**

1.  **Begin** — Use `/start` to join the Adventurer’s Guild and receive your Guild Card.
2.  **Prepare** — Manage your equipment and view your character’s Ledger.
3.  **Press Forward** — Choose a location and advance through it step by step:

- **Combat (60%)** — Auto-resolved battles narrated turn-by-turn.
   - **Regeneration (40%)** — You pause to breathe and recover HP/MP.

4.  **Field Pack** — Access inventory mid-adventure to equip items or use potions.
5.  **Withdraw to Astraeon City** — Return to the city to restore fully and finalize gains.
6.  **Advance** — Sell materials, complete quests, and rise through Guild Ranks (F → SSS).

---

# 🧩 **Major Features**

- Persistent **ONE UI** interface
- Manual, button-driven exploration
- Turn-by-turn combat playback (1.5s suspense delay)
- Auto-skill combat AI (class-aware decision making)
- Real HP/MP persistence with no auto-healing
- Material-based economy (no monster gold drops)
- Complete equipment + consumable system
- Inventory access during expeditions
- Guild Ranks with promotion requirements
- Quest Board + passive quest progression

---

# 🗂️ **Project Structure**

```
eldoria-bot/
├─ main.py                     # Bot entry point
├─ README.md
├─ requirements.txt
│
├─ cogs/
│ ├─ onboarding_cog.py         # /start, character creation
│ ├─ character_cog.py          # Profile, Ledger, Inventory, Skills UI
│ ├─ guild_hub_cog.py          # Guild Hall, Rank Up, Exchange
│ ├─ quest_hub_cog.py          # Quest Board + Quest Log UI
│ ├─ adventure_commands.py     # Main exploration and adventure UI
│ └─ ui_helpers.py             # Shared navigation functions
│
├─ database/
│ ├─ database_manager.py
│ ├─ create_database.py
│ └─ populate_database.py
│
├─ game_systems/
│ ├─ adventure/                # Exploration + session logic
│ ├─ combat/                   # Combat engine, phrases, math
│ ├─ data/                     # Classes, monsters, items, skills
│ ├─ guild_system/             # Exchange, ranks, quests, rewards
│ ├─ items/                    # Equipment & inventory managers
│ ├─ monsters/                 # Monster AI logic
│ └─ player/                   # Player stats + leveling
```

---

# 🛡️ **License & Ownership**

This project is **private intellectual property**.
All code, assets, systems, and lore belong solely to the creator.

**Not open-source. Not licensed for reuse or redistribution.**
