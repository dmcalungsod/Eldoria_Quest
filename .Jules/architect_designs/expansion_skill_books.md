# Expansion Blueprint: The Lost Tomes (Skill Books)

## 📖 Concept
Introduce horizontal progression and high-end replayability by adding rare consumable items—Skill Books—that permanently teach characters new skills or passives upon use. This system rewards engaging with difficult content (Rare, Elite, Boss, and Mythical monsters) and addresses current class imbalances (specifically the dominance of the Warrior class) by providing highly desirable, class-specific books for the Alchemist and Rogue.

**Theme:** "Forgotten knowledge is the ultimate survival tool." The Sundering destroyed libraries and lineages; recovering these techniques from the creatures that hoarded them is a major feat.

## 🎯 Design Goals
1.  **Incentivize High-Tier Combat:** Provide a chase item beyond standard materials (`magic_stone_flawless`, etc.).
2.  **Class Parity:** specifically buff the Alchemist and Rogue paths to be competitive with the 100% popularity Warrior class (per Analyst feedback) without directly nerfing the Warrior.
3.  **Horizontal Progression:** Allow players who have reached level caps or rank ceilings to continue growing their character's versatility.

## 📚 Mechanic Specifications

### 1. The Skill Book Item Type
*   **Item Type:** `consumable`
*   **Sub-type:** `skill_book`
*   **Behavior:** When consumed via the inventory, the book is destroyed, and the character permanently learns the associated skill. If the character already knows the skill, consumption fails and returns an error message ("You already possess this knowledge.").
*   **Class Restrictions:** Most books will have a `class_req` field. If a Warrior tries to read an Alchemist book, it fails.

### 2. Drop Logic (for GameBalancer & GameForge)
Skill books are meant to be exciting, rare drops.
*   **Normal Monsters:** 0% drop rate.
*   **Rare/Elite Monsters:** ~0.5% drop rate for Tier 1 / Base class books.
*   **Boss Monsters (e.g., Ignis, Tempest Guardian):** ~2% drop rate for specialized path books.
*   **Mythical / End-Game Bosses (e.g., Omega, The Void Heart, The Choirmaster):** ~5% drop rate for Ultimate/Legendary books.

## ✨ The Tomes (Class Parity Focus)

To ensure the Alchemist and Rogue are competitive with the Warrior, these specific books will drop from high-level content.

### The Rogue (Shadow's Edge Synergies)
The Rogue's weakness compared to the Warrior is sustained survivability in Auto-Adventures. These books provide alternative mitigations.

**1. Tome of the Shifting Sands (Phantom Path)**
*   **Teaches:** `mirage_stance` (Active Buff)
*   **Description:** "A stance that makes the user appear to be in multiple places at once."
*   **Mechanics:** Grants +100% AGI (Evasion) for 1 turn, but reduces ATK by 50% for that turn. Costs 15 MP.
*   **Target Drop:** Elite/Boss monsters in *The Shifting Wastes*.

**2. Manual of the Viper's Kiss (Assassin Path)**
*   **Teaches:** `toxic_catalyst` (Passive)
*   **Description:** "Poisons applied by the user act faster and deal more damage."
*   **Mechanics:** Increases all poison damage inflicted by the user by +50%.
*   **Target Drop:** Boss monsters in *The Undergrove*.

### The Alchemist (The Volatile Path Synergies)
The Alchemist needs ways to manage resources better and burst down threats to compete with Warrior DPS.

**1. Blueprint: Exothermic Reaction**
*   **Teaches:** `flash_fire` (Active AoE)
*   **Description:** "A rapid deployment of ignition powder, dealing low damage but applying a severe burn."
*   **Mechanics:** AoE attack (0.5x Power), applies Burn (5% Max HP/turn) for 3 turns. Costs 12 MP.
*   **Target Drop:** Ignis, Lord of Cinders (Boss - Molten Caldera).

**2. Notes on Cellular Regeneration**
*   **Teaches:** `synth_blood` (Passive)
*   **Description:** "The alchemist's own blood has been altered to coagulate rapidly."
*   **Mechanics:** Recovers 2% of Max HP every turn during combat.
*   **Target Drop:** Omega, The Void Heart (Boss - Void Sanctum) or The Choirmaster (Boss - Wailing Chasm).

## 🔗 Integration Notes

### 🛠️ For Tactician
1.  **Item Consumption Logic:** Update `ConsumableManager.use_item` to handle items where `type == "skill_book"`.
2.  **Skill Unlocking:** Implement a method (e.g., `Player.unlock_skill(skill_key)`) that appends the `skill_key` to the player's `learned_skills` list in the database. Ensure it checks class requirements and prevents duplicate learning.
3.  **Passive Evaluation:** Ensure the new passives (`toxic_catalyst`, `synth_blood`) are correctly evaluated in the `CombatEngine`.

### 🗄️ For DataSteward & GameForge
1.  **Item Data:** Create the new skill book items in `consumables.json`.
2.  **Skill Data:** Add `mirage_stance`, `toxic_catalyst`, `flash_fire`, and `synth_blood` to `skills.json`.
3.  **Loot Tables:** Add these items to the drop tables of the specified Elite/Boss monsters in `monsters.json`, adhering to the rare drop rates outlined above.

### ⚖️ For GameBalancer
1.  **Economy Review:** Ensure that these books are untradeable (or highly valued if tradeable) so they do not break the EV calculations for the associated zones.

### 📚 For ChronicleKeeper
1.  **Achievement:** "Forbidden Knowledge" - Read your first Skill Book.
2.  **Achievement:** "The Grand Library" - Read 5 Skill Books.
