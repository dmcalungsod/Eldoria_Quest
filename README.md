# 🌑 **Eldoria Quest**

### _A Dark High-Fantasy Survival RPG Discord Bot_

Inspired by:

- **Danmachi** — guild hierarchy, dungeon progression, steady advancement
- **Grimgar of Fantasy and Ash** — grounded danger, fragile mortality, material-driven survival
- **Literary fantasy** — atmospheric narration, immersive prose, worldbuilding through text

---

<p align="center">
  <img src="https://img.shields.io/badge/status-source%20available-darkgreen?style=flat"/>
  <img src="https://img.shields.io/badge/built_for-Discord-5865F2?style=flat&logo=discord&logoColor=white"/>
  <img src="https://img.shields.io/badge/license-All%20Rights%20Reserved-grey?style=flat"/>
</p>

<p align="center">
  <a href="https://dl.circleci.com/status-badge/redirect/gh/dmcalungsod/Eldoria_Quest/tree/main"><img src="https://dl.circleci.com/status-badge/img/gh/dmcalungsod/Eldoria_Quest/tree/main.svg?style=svg" alt="CircleCI"/></a>
  <a href="https://app.codacy.com?utm_source=gh&utm_medium=referral&utm_content=&utm_campaign=Badge_grade"><img src="https://app.codacy.com/project/badge/Grade/e81e8e2e775d4d758c20a3278d3aeeaa" alt="Codacy Badge"/></a>
  <a href="https://app.codacy.com?utm_source=gh&utm_medium=referral&utm_content=&utm_campaign=Badge_coverage"><img src="https://app.codacy.com/project/badge/Coverage/e81e8e2e775d4d758c20a3278d3aeeaa" alt="Codacy Badge"/></a>
  <img src="https://img.shields.io/badge/Python-3.13-3776AB?style=flat&logo=python&logoColor=white" alt="Python 3.13"/>
  <img src="https://img.shields.io/badge/MongoDB-47A248?style=flat&logo=mongodb&logoColor=white" alt="MongoDB"/>
  <a href="https://github.com/astral-sh/ruff"><img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json&style=flat" alt="Ruff"/></a>
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

### ⏳ Strategic Time Management

- **Respect Your Time:** The game shifts from manual grinding to strategic management.
- **Real-Time Expeditions:** Dispatch your character on adventures that resolve in real-time (30m - 24h).
- **Asynchronous Progression:** Your adventurer works while you do.

### 🜃 Narrative-Focused Immersion

- **Comprehensive Mission Reports:** Instead of spamming chat with turn-by-turn logs, you receive a detailed, literary summary of your journey upon return.
- **Deep Strategy:** Success depends on preparation (supplies, gear) and risk assessment, not button mashing.
- **Persistent State:** HP/MP and injuries persist between expeditions.

---

# 🜂 **Core Gameplay Loop**

1. **Begin** — Use `/start` to join the Adventurer’s Guild and receive your Guild Card.

2. **Prepare** — Manage equipment, inspect your Ledger, and stock up on Supplies (Rations, Torches).

3. **Dispatch** — Use `/adventure` to choose a destination and duration:
   - **Quick (30m):** Low risk, reliable resources.
   - **Long (8h+):** High risk, deep dungeon loot.

4. **Wait** — Your character explores the wilds in real-time. You are free to do other things.

5. **Report** — When the timer ends, receive a **Mission Report** detailing battles, loot found, and injuries sustained.

6. **Advance** — Return to Astraeon to heal, craft with new materials, and rise through Guild Ranks.

---

# 🧩 **Major Features**

- **Timeweaver Auto-Adventure System:** Asynchronous, time-based exploration.
- **Detailed Mission Reports:** Immersive summaries of off-screen combat and events.
- **Risk vs. Reward Scheduling:** Choose between safe, short trips or dangerous, long expeditions.
- **Strategic Supply Management:** Equip Rations and Torches to survive longer journeys.
- **Real HP/MP Persistence:** Injuries matter and require recovery.
- **Full Economy:** Crafting, Trading, and Guild Exchange.
- **One UI Architecture:** Clean, persistent interface without chat spam.

---

# 🗂️ **Project Structure**

```
eldoria-bot/
├─ main.py                          # Bot entry point
├─ README.md
├─ requirements.txt
│
├─ cogs/
│   ├─ onboarding_cog.py            # /start, character creation
│   ├─ character_cog.py             # Profile, Ledger, Inventory, Skills UI
│   ├─ adventure_cog.py             # Auto-Adventure Controller
│   ├─ guild_hub_cog.py             # Guild Hall, Rank Up, Exchange
│   ├─ quest_hub_cog.py             # Quest Board & Quest Log UI
│   ├─ shop_cog.py                  # Guild Shop UI
│   ├─ skill_trainer_cog.py         # Skill learning UI
│   ├─ status_update_cog.py         # Stat allocation UI
│   ├─ infirmary_cog.py             # Healing UI
│   └─ ui_helpers.py                # Shared navigation utilities
│
├─ database/
│   ├─ database_manager.py
│   ├─ create_database.py
│   └─ populate_database.py
│
├─ game_systems/
│   ├─ adventure/                   # Adventure system
│   │   ├─ ui/                      # Adventure UI views
│   │   ├─ adventure_manager.py
│   │   ├─ adventure_session.py
│   │   ├─ adventure_rewards.py
│   │   ├─ combat_handler.py        # Resolution engine logic
│   │   └─ event_handler.py
│   │
│   ├─ combat/                      # Combat engine core
│   │   └─ (combat modules...)
│   │
│   ├─ data/                        # Static data (monsters, items, etc.)
│   │   └─ (JSON, YAML, or Python dicts)
│   │
│   ├─ guild_system/                # Guild mechanics & logic
│   │   └─ ui/                      # Guild UI views
│   │
│   ├─ items/                       # Inventory & item logic
│   │   └─ (item modules...)
│   │
│   ├─ monsters/                    # Monster definitions & AI
│   │   └─ (monster modules...)
│   │
│   └─ player/                      # Player stats, leveling, skills, etc.
│       └─ (player modules...)
```

---

# 🛡️ **License & Ownership**

This project is **source-available** — the code is public for viewing and learning purposes.
All code, assets, systems, and lore are the intellectual property of the creator.

**No license is granted for reuse, redistribution, or modification.** See [LICENSE](LICENSE) for details.
