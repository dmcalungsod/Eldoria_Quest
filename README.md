# 🌑 **Eldoria Quest**

### _A Dark High-Fantasy Survival RPG Discord Bot_

Inspired by:

- **Danmachi** — guild hierarchy, dungeon progression, steady advancement
- **Grimgar of Fantasy and Ash** — grounded danger, fragile mortality, material-driven survival
- **Literary fantasy** — atmospheric narration, immersive prose, worldbuilding through text

---

<p align="center">
  <img src="https://img.shields.io/badge/status-private%20project-darkred?style=for-the-badge"/>
  <img src="https://img.shields.io/badge/built_for-personal%20use-blue?style=for-the-badge"/>
  <img src="https://img.shields.io/badge/not_open_source-grey?style=for-the-badge"/>
</p>

---

# 🜁 **World & Theme**

**Eldoria Quest** unfolds in a world fractured by **The Sundering** — a magical catastrophe that tore open the Veil and unleashed horrors across the realm.

Civilization clings to survival within fortified cities such as **Astraeon**, home to the **Adventurer’s Guild** — an institution forged out of necessity rather than glory. Adventurers are not celebrated heroes; they are laborers who brave the wilds so that Astraeon may endure.

Your character is officially registered with the Guild under the occupation of **Adventurer**, tasked with reclaiming the world one perilous step at a time.

The game blends:

- **Guild-driven structure** (Danmachi)
- **Material-based survival realism** (Grimgar)
- **Atmospheric, literary narration** woven into every action

---

# ⭐ **Design Philosophy**

### 🜄 Material-Driven Survival

- Monsters drop **Magic Stones** and **Monster Materials**, not gold.
- All Aurum is earned by selling these resources at the **Guild Exchange**.
- Every expedition is a risk; profit is never guaranteed.

### 🜃 Narrative-Focused Immersion

- Nearly the entire game unfolds within a single persistent **ONE UI** interface.
- Exploration is **manual**, deliberate, and turn-based.
- Every action is narrated with thematic, class-aware writing.
- HP/MP persist between encounters — recovery is scarce and meaningful.

---

# 🜂 **Core Gameplay Loop**

1. **Begin** — Use `/start` to join the Adventurer’s Guild and receive your Guild Card.

2. **Prepare** — Manage equipment, inspect your Ledger, and ready yourself.

3. **Press Forward** — Choose a location and advance through it step by step:

   - **Combat (60%)** — Auto-resolved encounters narrated turn-by-turn.
   - **Regeneration (40%)** — Short rests where you recover HP/MP.

4. **Field Pack** — Access inventory mid-expedition to equip items or use consumables.

5. **Return to Astraeon** — Recover fully, sell materials, and tally your gains.

6. **Advance** — Earn Aurum, complete quests, and rise through Guild Ranks (F → SSS).

---

# 🧩 **Major Features**

- Persistent **ONE UI** interface
- Manual, button-driven exploration
- Turn-by-turn combat playback with suspense timing
- Auto-skill combat AI (class-aware)
- Real HP/MP persistence (no natural regeneration)
- Full equipment + consumable system
- Inventory access during expeditions
- Guild Ranks with structured promotion
- Quest Board + passive quest progression

---

# 🗂️ **Project Structure**

```
eldoria-bot/
├─ main.py                     # Bot entry point
├─ README.md
├─ requirements.txt
│
├─ cogs/
│ ├─ onboarding_cog.py         # /start, character creation
│ ├─ character_cog.py          # Profile, Ledger, Inventory, Skills UI
│ ├─ guild_hub_cog.py          # Guild Hall, Rank Up, Exchange
│ ├─ quest_hub_cog.py          # Quest Board + Quest Log UI
│ ├─ adventure_commands.py     # Main exploration & adventure UI
│ └─ ui_helpers.py             # Shared navigation utilities
│
├─ database/
│ ├─ database_manager.py
│ ├─ create_database.py
│ └─ populate_database.py
│
├─ game_systems/
│ ├─ adventure/                # Exploration logic + session state
│ ├─ combat/                   # Combat engine, math, narration
│ ├─ data/                     # Classes, monsters, items, skills
│ ├─ guild_system/             # Exchange, ranks, quests, rewards
│ ├─ items/                    # Equipment and inventory logic
│ ├─ monsters/                 # Monster behavior + AI
│ └─ player/                   # Player stats, progression, occupation
```

---

# 🛡️ **License & Ownership**

This project is **private intellectual property**.
All code, assets, systems, and lore belong solely to the creator.

**Not open-source. Not licensed for reuse or redistribution.**
