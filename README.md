# 🌑 **Eldoria Quest**

### _A Dark High-Fantasy Idle RPG Discord Bot_

Inspired by guild-based progression, grounded survival themes, and atmospheric literary fantasy

---

\<p align="center"\>
\<img src="[https://img.shields.io/badge/status-private%20project-darkred?style=for-the-badge](https://img.shields.io/badge/status-private%20project-darkred?style=for-the-badge)"/\>
\<img src="[https://img.shields.io/badge/built_for-personal_use-blue?style=for-the-badge](https://img.shields.io/badge/built_for-personal_use-blue?style=for-the-badge)"/\>
\<img src="[https://img.shields.io/badge/not_open_source-grey?style=for-the-badge](https://img.shields.io/badge/not_open_source-grey?style=for-the-badge)"/\>
\</p\>

---

# 🜁 **The Theme of Eldoria Quest**

**Eldoria Quest** is a private, personal RPG system built as a fully immersive **Dark High-Fantasy Idle RPG**.

The world is shaped by **The Sundering**—a cataclysm that shattered the Veil “like weathered glass,” unleashing nightmares upon the fractured lands of Eldoria. Civilization now clings to fortified enclaves, and the **Adventurer's Guild** stands as humanity’s last defense.

The experience blends:

- **Guild Progression** — adventurer ranks and a structured advancement system
- **Grounded Survival** — a focus on tone, emotional weight, and realism
- **Classic literary fantasy** — atmospheric narration, slow-burn storytelling

This is not a typical power fantasy—its tone is gritty, grounded, and unforgiving.

---

# ⭐ **Design Philosophy**

### **Grounded Adventuring**

- Early-game danger reflects a realistic survival tone
- Monsters hit hard
- Supplies and stamina matter
- Death ends the adventure and shapes the story

### **Emotional, Earned Progression**

- No magical coin drops—only scavenged monster parts
- All currency (Aurum) is earned through Guild Exchange
- Each stat point feels meaningful
- Growth is slow, narratively grounded

### **Literary, Atmospheric Narration**

Every message is styled like a fantasy novel:

> _“You steady your breathing as the mist thins before you.
> The boundary stone hums faintly, a reminder that one misstep can end a novice’s life.”_

---

# 🜂 **Core Gameplay Loop**

### **1. Player Registration**

Players register with the **Adventurer's Guild**
and receive their **Guild Card**—their identity and lifeline.

---

### **2. Choosing a Quest**

The Quest Board presents simple but dangerous tasks:

- Slime extermination
- Gathering beast pelts
- Scouting ruined outskirts
- Boundary patrols

These are low-tier but deadly—reflecting the struggles of a new adventurer.

---

### **3. Idle Adventure**

Players select:

- A zone
- An adventure duration (minutes → hours)

The bot simulates encounters **every 5 minutes**, outputting combat logs in a slow, atmospheric rhythm.

---

### **4. Loot-Only Economy**

Enemies drop:

- Monster hides
- Fangs, claws, bones
- Magic stones
- Corrupted essences
- Shards & fragments

Materials must be **sold manually** at the **Guild Exchange**
—a core part of the realistic economy.

---

### **5. Survival & Consequences**

Death:

- Ends an adventure early
- Generates a harsh but narratively immersive summary
- Carries real tension and weight

---

# 6\. Slow Progression

Players level up over time through:

- Incremental stat gains
- Skill unlocks
- Attribute growth
- Guild Merit increases

The pace is deliberate—not a power fantasy.

---

# 🧩 **Major Features**

### ✔️ Detailed guild ranking system

### ✔️ Scavenging-based economy

### ✔️ Idle auto-adventure system

### ✔️ Real-time interval combat (every 5 minutes)

### ✔️ Material drops instead of currency

### ✔️ Sell items for Aurum at the Guild Exchange

### ✔️ Detailed level & stat tracking

### ✔️ Atmospheric narration for every event

### ✔️ Robust modular system architecture

---

# 🗂️ **Project Structure (Private Layout)**

```
/game_systems
    /adventure_system
        adventure_manager.py
        adventure_session.py
    /combat_system
        combat_engine.py
        monster_data.py
    /guild_system
        reward_system.py
        rank_system.py
    /quest_system
        quest_system.py
    /inventory_system
        inventory_manager.py

/database
    database_manager.py
    schema.sql

/ui
    guild_card_ui.py
    menu_buttons.py

config/
    config.py
    constants.py

bot.py
README.md
```

_(Only a structural overview — this repository is private and not intended for external use.)_

---

# ⚙️ **Setup (Private Use Only)**

Because this is a personal, closed-source project, setup instructions are intentionally minimal.

### **1. Install Required Libraries**

Python 3.10+ recommended.

```
pip install -r requirements.txt
```

### **2. Configure Environment Variables**

In `.env`:

```
DISCORD_TOKEN=your_private_token_here
```

### **3. Initialize Local Database**

Run:

```
python database/setup_database.py
```

### **4. Launch the Bot**

```
python bot.py
```

---

# ✨ **Core Bot Commands**

### Adventurer Commands

- `/start` — Register as an adventurer
- `/status` — View detailed adventurer status
- `/profile` — Open Guild Card UI

### Progression & Tasks

- `/questboard` — Browse quests
- `/adventure` — Begin idle exploration
- `/inventory` — View collected materials
- `/exchange` — Trade materials for Aurum

---

# 🔮 **Future Enhancements (Internal Roadmap)**

- Multi-party dungeon expeditions
- Personality-driven AI party members
- Dynamic events based on zone corruption levels
- Crafting and forging systems
- Skill trees & specializations
- S-Rank boss hunts
- Seasonal events
- Procedural story arcs

---

# 🛡️ **License & Ownership**

This repository is **private intellectual property**.
All code, design, mechanics, lore, and documentation belong exclusively to the project owner.

**Not open-source.
Not licensed for public distribution or reuse.**

---

# 🜸 **Final Notes**

Eldoria Quest is a personal passion project built for immersion, mood, and grounded fantasy storytelling.
It blends:

- A structured guild system
- Grounded, realistic progression
- Literary dark-fantasy prose
