# 📜 Quest: The Great Work (Alchemist Class Introduction)

## 🎭 Giver
**Alchemist Miral**
*   **Location:** The Shrouded Fen (Alchemist's Camp)
*   **Personality:** Brilliant, obsessive, slightly unhinged. Views the Veil-sickness as a fascinating biological problem rather than a tragedy. Uses scientific jargon mixed with occult terms.

## 📖 Story
Miral believes she can cure the Veil-sickness by transmuting the corruption within living creatures. She needs a field assistant to gather volatile reagents and test her experimental serums. The questline explores the ethical boundary between scientific progress and the sanctity of life.

## 🗺️ Quest Chain

### 1. Volatile Ingredients (ID: 70)
*   **Rank:** F
*   **Summary:** Gather acidic spores for Miral's research.
*   **Objective:** Defeat 5 Sporelings (Flavor: Collecting acidic residue).
*   **Hook:** Miral is too busy (or smart) to risk her own skin gathering dangerous materials.

### 2. The Great Work: Hypothesis (ID: 71)
*   **Rank:** E
*   **Prerequisite:** Quest 70
*   **Summary:** Secure a test subject.
*   **Objective:** Defeat 1 Mire Lurker (Flavor: Subduing and capturing it alive for study).
*   **Conflict:** Druidess Leira intervenes, warning that Miral's serums torture the beasts and create abominations. She asks you to mercy-kill the creature instead.

### 3. Branching Choice (ID: 72 / 73)
The player must choose how to proceed with the captured/targeted Mire Lurker. Both quests use the "Defeat" objective mechanic but represent different narrative actions via flavor text.

#### Option A: Evolution (Science) - Quest ID 72
*   **Choice:** "Administer the serum as Miral commanded."
*   **Narrative:** You prioritize the potential cure over the creature's suffering.
*   **Objective:** Defeat 1 Mire Lurker (Flavor: Administering serum which causes fatal mutation).
*   **Reward:** **Thicket Antidote**, Reputation with Alchemists (Narrative).
*   **Consequence:** Miral is ecstatic. Leira is disgusted.

#### Option B: Preservation (Nature) - Quest ID 73
*   **Choice:** "Euthanize the beast as Leira requested."
*   **Narrative:** You prioritize the balance of nature and mercy.
*   **Objective:** Defeat 1 Mire Lurker (Flavor: A clean, merciful kill).
*   **Reward:** **Glade Salve Vial**, Reputation with Druids (Narrative).
*   **Consequence:** Miral is annoyed but accepts the data point ("Death is also a transformation"). Leira is grateful.

## 🏆 Rewards
*   **EXP:** Scaled for Rank F/E (400-900)
*   **Aurum:** Moderate (100-400)
*   **Items:** Consumables related to Alchemy/Nature.

## 🤝 Coordination
*   **GameForge:** `exclusive_group` logic is confirmed to be supported by `QuestSystem`.
*   **StoryWeaver:** Dialogue for Miral needs to be punchy and "mad scientist".
*   **Namewright:** "Mutagenic Serum 0.1" is a working title.
*   **Technical Note:** Quests use standard `defeat` objectives to ensure compatibility with existing `QuestSystem` logic without requiring code changes.
