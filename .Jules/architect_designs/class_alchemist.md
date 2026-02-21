# Class Design: Alchemist

## 🎭 Concept
**"While mages study the stars, I study the dirt."**

The Alchemist is a pragmatic survivor who uses the remnants of the world to fight back against the darkness. They are not magical in the traditional sense; their power comes from knowledge of monster anatomy, volatile compounds, and desperate ingenuity. They are a mid-range fighter who excels at weakening enemies and dealing consistent damage through chemical warfare.

## 📜 Lore (for StoryWeaver)
In the wake of the Sundering, traditional magic became erratic and dangerous. Those who refused to rely on fickle leylines turned to the physical world—extracting venom from slain beasts, distilling explosive salts from the earth, and stitching wounds with sterile thread. Alchemists are often viewed with suspicion, seen as scavengers or graverobbers, but when a plague spreads or a beast needs to be brought down, their concoctions are worth more than gold.

## 📊 Base Stats (for GameBalancer)
The Alchemist relies on **DEX** (precision in throwing/mixing) and **MAG** (knowledge of potency), with decent **LCK** (finding ingredients). They are less durable than a Warrior but hardier than a Mage due to their chemical enhancements.

- **STR**: 3 (Low)
- **END**: 5 (Medium)
- **DEX**: 7 (High - Primary Offensive Stat)
- **AGI**: 4 (Medium-Low)
- **MAG**: 6 (High - Potency Stat)
- **LCK**: 5 (High - Scavenging)

**Starting Equipment:**
- **Weapon**: Rusty Dagger (or "Alchemist's Scalpel")
- **Offhand**: Cracked Vial (if dual-wield logic allows)
- **Armor**: Leather Apron (Medium Armor)
- **Misc**: Basic Bandages

## ⚔️ Skill Tree: The Chemist's Art

### Tier 1 (Rank F)
#### **Acid Flask** (Active)
*Throw a vial of corrosive acid that burns the target and weakens their armor.*
- **Type**: Active
- **Cost**: 8 MP
- **Scaling**: DEX (Aim) + MAG (Potency)
- **Effect**: Moderate Damage + **Defense Break** (Reduces target DEF by 20% for 3 turns).
- **Narrative**: "Glass shatters, and the hiss of dissolving metal fills the air."

#### **Field Triage** (Active)
*Quickly apply a healing salve to close wounds.*
- **Type**: Active (Heal)
- **Cost**: 10 MP
- **Scaling**: MAG
- **Effect**: Restores HP (Moderate).
- **Narrative**: "A sharp sting of alcohol, then the bleeding stops."

### Tier 2 (Rank D)
#### **Volatile Brew** (Active)
*Hurl an unstable mixture that explodes on impact.*
- **Type**: Active (AoE)
- **Cost**: 15 MP
- **Scaling**: MAG
- **Effect**: High Damage to all enemies.
- **Narrative**: "You shake the flask until it glows, then throw it before it takes your hand off."

#### **Scavenger's Intuition** (Passive)
*You know exactly where to look for the good stuff.*
- **Type**: Passive
- **Effect**: +15% LCK.
- **Narrative**: "One man's trash is an Alchemist's arsenal."

### Tier 3 (Rank C)
#### **Adrenal Injector** (Active)
*Inject a risky stimulant to boost physical performance.*
- **Type**: Active (Buff)
- **Cost**: 20 MP
- **Effect**: +30% STR, +30% AGI for 3 turns. Self-inflict minor damage (10 HP)?
- **Narrative**: "The heart hammers like a drum, and the world moves in slow motion."

## 🔗 Integration Notes

### 🧠 Tactician (Combat Systems)
- **New Mechanic Needed**: **Player-Inflicted Debuffs**.
  - Currently, `CombatEngine` does not parse `debuff` keys from player skills effectively (unlike `MonsterAI`).
  - Please implement support for `defense_break` (reducing monster DEF) in `CombatEngine` and `DamageFormula`.
- **New Mechanic Needed**: **Self-Damage Costs**.
  - `Adrenal Injector` suggests a "HP Cost" or self-damage component for high-risk buffs.

### 🛠️ GameForge (Items & Monsters)
- **New Weapon Type**: Consider adding "Satchels" or "Vials" as a weapon type, or skin Daggers as "Scalpels".
- **Class Quest**: "The Alchemist's Debt" – A quest to collect rare monster parts to brew a cure for a dying NPC.

### 📖 ChronicleKeeper (Achievements)
- **Achievement**: "Mad Science" – Kill 50 enemies with `Volatile Brew`.
- **Title**: "Plague Doctor" – Unlock all Alchemist skills.

### ⚖️ Grimwarden (Tone Check)
- Ensure skill descriptions emphasize the *chemical/physical* nature, not magical. It's about reactions, not incantations.
