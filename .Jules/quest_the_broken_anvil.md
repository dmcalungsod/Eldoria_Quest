# Quest Design: The Broken Anvil

**Designer:** Questweaver
**Status:** Ready for Implementation
**Target Rank:** A (Level 30+)

## Core Identity
- **Quest Name:** The Broken Anvil
- **Giver NPC:** Magni the Anvil, Head of the Forge-Masters (A gruff, imposing smith whose right arm is replaced by a massive, articulated Star Metal prosthetic. He smells perpetually of brimstone and sweat.)
- **Location:** The Deep Forges (Ironhaven)
- **Prerequisites:** Rank A, must have access to Ironhaven.

## Narrative Elements
- **Hook:** The central forge of Ironhaven, the Aegis-Heart, is dying. Its core anvil, carved from a single piece of Frost-forged Steel, has cracked under the relentless demand of the war effort against the Void.
- **Rising Action:** Magni needs a replacement block of raw, super-cooled Star Metal, which can only be found deep within the Howling Peaks, guarded by Frost Gargoyles. But simply bringing the ore isn't enough; it must be quenched in the blood of a Storm Drake to temper it properly for the Aegis-Heart.
- **Climax:** A two-part challenge: First, mining the heavy ore from a dangerous node. Second, hunting a Storm Drake and surviving its lightning-infused breath to harvest its blood.
- **Resolution:** A difficult choice upon returning to Magni. The player discovers that another faction, the Drake-Riders, desperately needs the Star Metal to reinforce their Aviary Towers before an impending Void swarm.

## Dialogue Script

### Start
*The heat of the Deep Forges is oppressive, but Magni the Anvil stands before the massive, sputtering Aegis-Heart forge without sweating. He strikes a cracked, glowing anvil, then throws his hammer down in disgust.*

**Magni:** "Useless! The Frost-forged steel is giving out. The Aegis-Heart is dying, and if it dies, the Vanguard's shields will shatter in the next assault."
**Player:** "What do you need?"
**Magni:** "A miracle. Or a block of raw Star Metal from the highest ridges of the Howling Peaks. But don't just bring me the rock. It's too brittle on its own. It needs to be quenched in the blood of a Storm Drake to bind the magic."
**Player Option A:** "I'll get your metal and the blood." (Accepts quest)
**Player Option B:** "I don't have time to run errands for a blacksmith." (Refuses)

### Mid-Quest (Optional Return without items)
**Magni:** "Where is the metal? The crack is widening. If you can't handle the peaks, step aside and let a real Vanguard do it."

### Climax (Upon returning with items)
*As you approach Magni with the heavy Star Metal and the vial of crackling Drake Blood, General Rask of the Iron Vanguard intercepts you.*

**Rask:** "Hold, adventurer. Magni wants that metal to save his precious forge. But the Aviary Towers are taking heavy damage. We need that Star Metal to reinforce the roosts, or the Drake-Riders won't be able to launch. The skies will fall."
**Magni:** (storming over) "The shields come first, Rask! If the ground falls, your birds won't have anywhere to land!"

**Player Option A (Give to Magni):** "The forge is the heart of this city. Take it, Magni."
**Player Option B (Give to Rask):** "Control the skies, control the battle. Use it for the Aviary, General."

### Resolution (Option A - Magni)
*Magni snatches the ore and blood, his prosthetic arm whirring as he hurls them into the Aegis-Heart. The forge roars back to life, blazing with a blinding, blue-white intensity.*
**Magni:** "Good choice. The Vanguard's shields will hold against the Void. You've got the soul of a smith, adventurer. Keep this. It's a prototype from the new batch."

### Resolution (Option B - Rask)
*Rask nods grimly and takes the supplies, gesturing for his runners to take them to the Aviary.*
**Rask:** "A tactical mind. The skies will remain ours. The Forge-Masters will just have to make do. You've earned the Vanguard's respect."

## Objectives
1.  **Objective 1:** Travel to the Howling Peaks and defeat Frost Gargoyles until you find the hidden node. (Defeat 3 Frost Gargoyles)
2.  **Objective 2:** Mine the Star Metal. (Collect 1 Raw Star Metal Block)
3.  **Objective 3:** Hunt a Storm Drake and harvest its blood. (Defeat 1 Storm Drake, Collect 1 Vial of Drake Blood)
4.  **Objective 4:** Return to the Deep Forges and make your choice.

## Rewards
-   **Completion:** 8500 EXP, 3000 Aurum.
-   **Choice A (Magni):** +20 Forge-Masters Reputation, 1x "Frost-forged Bulwark" (Shield), Title: "The Anvil's Spark".
-   **Choice B (Rask):** +20 Iron Vanguard Reputation, 1x "Storm-Chaser's Mantle" (Cloak), Title: "Sky Warden".

## Agent Coordination
-   **GameForge:** Implement the objectives in `quests.json` and the quest items (`raw_star_metal_block`, `vial_of_drake_blood`) in `quest_items.json`.
-   **Grimwarden/Tactician:** Ensure Storm Drakes and Frost Gargoyles are present in the Howling Peaks with appropriate difficulty for Rank A.
-   **ChronicleKeeper:** Could add an achievement for completing this questline.
-   **StoryWeaver:** Review dialogue for tone.
