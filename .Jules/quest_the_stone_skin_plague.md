# Quest Design: The Stone-Skin Plague

**Theme:** Grim Survival / Medical Horror
**Faction:** Grey Ward
**Rank:** D (Level 12+)
**Location:** Deepgrove Roots / The Ashlands

## 📖 Narrative Arc
A strange affliction is turning the refugees of the outer districts into statues. The Grey Ward, Eldoria's pragmatic alchemists, are overwhelmed. They need an adventurer to trace the source and secure a cure before the "Stone-Skin" spreads to the inner city.

## 📜 Quest List

### 1. **The Stone-Skin Symptoms** (ID: 74)
*   **Giver:** Alchemist Vane (Grey Ward Field Medic)
*   **Location:** Deepgrove Roots
*   **Summary:** Collect tissue samples from petrified wildlife.
*   **Objectives:**
    *   `collect`: "Petrified Heart" x3 (from Stone-Cursed Wolves/Boars)
    *   `examine`: "Calcified Corpse" x1
*   **Flavor Text:**
    *   *collect*: "The heart is heavy and cold, turned completely to grey stone."
    *   *examine*: "The victim's face is frozen in a silent scream. Moss is already growing in the cracks."
*   **Rewards:** 600 EXP, 150 Aurum, Item: "Grey Ward Mask" (Vanity/Lore item)

### 2. **The Basilisk's Bile** (ID: 75)
*   **Giver:** Alchemist Vane
*   **Prerequisite:** ID 74
*   **Location:** The Ashlands (Border)
*   **Summary:** Hunt a Basilisk to extract its bile for the antidote.
*   **Objectives:**
    *   `defeat`: "Ash Basilisk" x1 (New/Existing Monster or flavor rename of a lizard)
    *   `collect`: "Basilisk Bile" x1
*   **Flavor Text:**
    *   *defeat*: "The beast hisses one last time before dissolving into ash."
    *   *collect*: "The bile smokes in the vial, smelling of acid and old earth."
*   **Rewards:** 800 EXP, 200 Aurum, Item: "Unstable Antidote"

### 3. **The Cure: For the Few** (ID: 76) -- **CHOICE A**
*   **Giver:** Merchant Gilded-Tongue
*   **Prerequisite:** ID 75
*   **Exclusive Group:** `stone_skin_choice`
*   **Summary:** Sell the antidote to a wealthy noble house who fears infection.
*   **Dialogue:** "Why waste such a miracle on the dregs? House Valerius will pay a fortune. They can replicate it... eventually. Secure your future, adventurer."
*   **Objectives:**
    *   `deliver`: "Unstable Antidote" to "House Valerius Courier"
*   **Rewards:** 1500 Aurum, 400 EXP. **consequence:** Grey Ward Rep penalty (invisible but thematic), "Mercenary" title.

### 4. **The Cure: For the Many** (ID: 77) -- **CHOICE B**
*   **Giver:** Alchemist Vane
*   **Prerequisite:** ID 75
*   **Exclusive Group:** `stone_skin_choice`
*   **Summary:** Hand the antidote to the Grey Ward to synthesize a mass cure for the refugees.
*   **Dialogue:** "It's not enough for everyone yet, but with this sample, we can save the quarantine zone. You did good. Real good."
*   **Objectives:**
    *   `deliver`: "Unstable Antidote" to "Alchemist Vane"
*   **Rewards:** 500 Aurum, 1000 EXP, **Grey Ward Rep +250**, Item: "Alchemist's Retort" (Crafting Station/Item).

## 🛠️ Implementation Details
*   **New Items:**
    *   `q_petrified_heart` (Quest Item)
    *   `q_basilisk_bile` (Quest Item)
    *   `q_unstable_antidote` (Quest Item)
*   **Monsters:**
    *   Use existing `Ash Rat` or `Ember Fox` stats but flavor text implies they are "Stone-Cursed".
    *   For the Basilisk, use `Ember Salamander` (ID 108) stats or `Scorched Scavenger` (ID 134) as a placeholder if a unique mob isn't created.
