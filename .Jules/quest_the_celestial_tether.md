# Quest: The Celestial Tether

**Giver:** Archivist Thorne, Guild Library (Analytical but deeply concerned. He sees the historical value of Aethoria but is terrified of its imminent collapse.)
**Prerequisite:** Rank B, no prior Aethoria quests required

## Hook
The ancient floating ruins of Aethoria, known to adventurers as The Celestial Archipelago, are losing altitude. Star-metal debris has started raining down on the outer settlements, destroying a watchtower. Archivist Thorne suspects the magic supporting the city is failing.

## Dialogue (Start)
*Archivist Thorne is hunched over a scattering of scorched star-metal fragments. He doesn't look up as you approach.*

**Thorne:** "Another one fell last night. Crushed the eastern watchtower. If the Central Spire goes, the entire Archipelago will follow. Thousands of tons of stone and metal, directly onto the Wastes... and us."
**Player:** "What's causing it to fall?"
**Thorne:** "The gravity tethers are failing. The Arch-Mages who raised Aethoria are long dead, and the magic is starving. You need to ascend to the Central Spire and investigate the Celestial Core. Either find a way to stabilize it, or... well, let's pray it can be stabilized."
**Player Option A:** "I'll climb the Spire and see what can be done." (Accepts quest)
**Player Option B:** "Falling cities aren't my problem." (Refuses, can return later)

## Objectives (Part 1: Falling Stars)
1. Ascend to The Celestial Archipelago.
2. Gather: Star Metal Fragment (3) (from fallen debris) → Gain clue "Failing Magic Resonance"
3. Defeat: Sky-Ray (5) (Clearing the lower platforms of aerial predators)
4. Locate: The Central Spire (Ascending to the heart of Aethoria)

## Dialogue (Mid‑Quest – Optional Return)
**Thorne:** "The fragments you found... they're completely drained of mana. Whatever is happening up there, it's consuming everything. Hurry, adventurer."

## Climax
Upon reaching the Central Spire, you find the colossal, dormant **Celestial Arbiter**, a massive construct guarding the failing Celestial Core. The core is cracked and leaking volatile energy.

*The Arbiter's voice echoes in your mind, a mechanical monotone devoid of emotion.*
**Celestial Arbiter:** "WARNING. TETHER INTEGRITY AT 12%. CORE INSTABILITY IMMINENT. INITIATING PURGE PROTOCOL."

**Player Option A (Preserve):** "I can repair the tether. Take these Aether Stones." (Initiates defense event)
**Player Option B (Plunder):** "The city is doomed anyway. I'm taking the core." (Initiates boss fight)

## Resolution (Choice A: Preserve)
*If the player chooses to repair the tether, they must defend the Arbiter from waves of Arcane Sentinels attempting to purge the "unauthorized repair."*

*After the defense:*
**Celestial Arbiter:** "AETHER STONES ACCEPTED. TETHER INTEGRITY RESTORED TO 84%. AETHORIA SHALL REMAIN ALOFT."

*Returning to Thorne:*
**Thorne:** (Exhales deeply, wiping his brow) "The readings... the descent has stopped. You saved Aethoria. And you saved us. The Guild owes you a debt we cannot easily repay."

## Resolution (Choice B: Plunder)
*If the player chooses to plunder, they must destroy the Celestial Arbiter and rip the core from the machine.*

*After the fight:*
**Celestial Arbiter:** "CRITICAL ERROR... CORE BREACH... AETHORIA... FALLING..."

*Returning to Thorne:*
**Thorne:** (Staring at the glowing core in your hands, his face pale) "You... you tore it out? By the Gods, adventurer, do you realize what you've done? The city's descent is accelerating! We have weeks, maybe less, before the impact. You've doomed a wonder of the old world for a piece of shiny rock."

## Rewards
- **Falling Stars (Part 1):** 4500 EXP, 1200 Aurum
- **Preserve (Choice A):** 6000 EXP, 1500 Aurum, "Aethorian Ward Recipe" (Trinket), Title "The Sky Warden"
- **Plunder (Choice B):** 7500 EXP, 3000 Aurum, "Fractured Celestial Core" (High-value material/Trinket), Title "Gravity's End"

## Choices & Consequences
- **Choice A (Preserve):** The ruins remain stable in the lore. Thorne is relieved. The player gains a defensive trinket recipe.
- **Choice B (Plunder):** The city's descent accelerates in the lore (setting up a potential future world event where it crashes). Thorne is disgusted, resulting in a permanent dialogue change where he treats the player coldly. The player gains a powerful offensive material.

## Agent Coordination
- **StoryWeaver:** Use these dialogue scripts to implement the quest text.
- **GameForge:** Ensure "Sky-Ray", "Arcane Sentinel", and "The Celestial Arbiter" exist in `monsters.json`. Implement the branching quests using `exclusive_group`.
- **Equipper:** Add "Aethorian Ward Recipe" and "Fractured Celestial Core".
- **DepthsWarden/Realmwright:** Ensure The Central Spire is a recognized sub-location.
- **ChronicleKeeper:** Add achievements for preserving Aethoria ("The Sky Warden") and for dooming it ("Gravity's End").
