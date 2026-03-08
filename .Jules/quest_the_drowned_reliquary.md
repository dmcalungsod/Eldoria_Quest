# Quest Design: The Drowned Reliquary

**Designer:** Questweaver
**Status:** Ready for Implementation
**Target Rank:** A (Level 30+)

## Core Identity
- **Quest Name:** The Drowned Reliquary
- **Giver NPC:** Captain "Iron-Lung" Thade (Leader of the Deep Salvagers. He is scarred from decompression sickness, speaks with a wet wheeze, and views the Guild with deep suspicion.)
- **Location:** The Flooded Atrium (The Sunken Grotto)
- **Prerequisites:** Rank A, `Abyssal Rebreather` equipped, Rank 1 (Scavenger) with the Deep Salvagers.

## Narrative Elements
- **Hook:** Thade’s crew found something in the Sunken Reliquary, the deepest part of the ruins. It isn't just treasure; it's a massive, pulsating Pearl of Luminous Tide. But the expedition was wiped out by The Leviathan's Shadow, and the pearl remains trapped.
- **Rising Action:** The player must dive deep, navigating the Murmuring Depths and dealing with the treacherous currents and Tide-Stalkers. Along the way, they find the drowned bodies of Thade's crew, gathering their scattered notes which hint that the Pearl is actually a seal keeping a greater Void breach closed.
- **Climax:** The player reaches the Sunken Reliquary. They must fight off an Abyssal Siren and several Coral-Bound Goliaths while maintaining their oxygen levels to reach the Pearl.
- **Resolution:** A moral choice. The player holds the Pearl. They can either take it to Thade for immense wealth and standing with the Salvagers, breaking the seal and slightly increasing the spawn rate of Void-touched enemies in the Grotto, or they can leave it in place, restoring the seal but returning to Thade empty-handed.

## Dialogue Script

### Start
*Captain Thade coughs violently, a wet, rattling sound, before fixing you with a milky eye.*

**Thade:** "You think because you got that shiny Guild badge you can survive the deep? The Grotto doesn't care about ranks. It only cares about how long you can hold your breath."
**Player:** "I've handled worse than water."
**Thade:** "Water isn't the problem. It's what's *in* it. My best crew went down to the Sunken Reliquary. Found a Pearl the size of a man's head. But the Leviathan's Shadow woke up. Only one came back, and he died babbling about a 'pulsating tide'. I want that Pearl. Get it, and you'll be a Reef Walker to us. Fail, and you'll just be chum."
**Player Option A:** "I'll dive down and get your Pearl." (Accepts quest)
**Player Option B:** "I'm not risking my neck for shiny rocks." (Refuses)

### Mid-Quest (Finding the Crew's Notes)
*You find a waterlogged journal clutched in the hand of a drowned Salvager.*
**Journal Text:** "It's not a jewel. The Pearl... it's humming. It's plugging a crack in the ocean floor. Black water is seeping out. If we move it, the whole trench might tear open."

### Climax (Upon reaching the Pearl)
*The Pearl of Luminous Tide rests on an ancient altar, pulsing with a gentle, purifying light against a backdrop of swirling, inky Void energy trying to push through the stone.*

**Player Option A (Take the Pearl):** "Thade promised a fortune for this. The Void is the Vanguard's problem."
**Player Option B (Leave the Pearl):** "The seal must hold. Thade will just have to live without it."

### Resolution (Option A - Take the Pearl)
*You pry the Pearl loose. Immediately, the water around you turns frigid and dark, the Void seeping through the new crack. You return to Thade.*
**Thade:** "You... you actually did it! Look at the size of it! We'll live like kings in Ironhaven. You're one of us now, deep-diver."

### Resolution (Option B - Leave the Pearl)
*You channel your own mana to reinforce the Pearl's light. The dark crack seals shut, the water clearing slightly. You return to Thade empty-handed.*
**Thade:** "Empty hands? After all that talk? You Guild types are all the same. Afraid of a little risk."
**Player:** "It was a seal holding back the Void. Moving it would have doomed this whole region."
**Thade:** "Doomed? We're already doomed! The only difference is whether we die rich or poor. Get out of my sight."

## Objectives
1.  **Objective 1:** Descend into the Murmuring Depths.
2.  **Objective 2:** Find the drowned crew and recover their notes. (Collect 3 Waterlogged Journals)
3.  **Objective 3:** Reach the Sunken Reliquary and defeat the guardians. (Defeat 1 Abyssal Siren, Defeat 2 Coral-Bound Goliaths)
4.  **Objective 4:** Make your choice regarding the Pearl of Luminous Tide.
5.  **Objective 5:** Return to Captain Thade.

## Rewards
-   **Completion:** 10000 EXP, 2000 Aurum.
-   **Choice A (Take the Pearl):** +50 Deep Salvagers Reputation, 1x "Luminous Pearl" (Rare Crafting Material), Title: "Abyssal Plunderer", *Hidden Effect: Minor increase to Void monster spawns in Sunken Grotto.*
-   **Choice B (Leave the Pearl):** +20 Guild Reputation, -20 Deep Salvagers Reputation, 1x "Current Rider's Band" (Accessory), Title: "Warden of the Deep".

## Agent Coordination
-   **GameForge:** Implement the objectives in `quests.json` and the quest items (`waterlogged_journal`) in `quest_items.json`.
-   **DepthsWarden:** Ensure the "Deep Salvagers" faction handles the reputation changes appropriately.
-   **Equipper:** Ensure the "Current Rider's Band" is added to `equipments.json`.
-   **GameBalancer:** Note the slight shift in spawn rates for Choice A, if dynamically possible in the engine.
-   **StoryWeaver:** Review dialogue for tone.
