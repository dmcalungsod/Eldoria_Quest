# Quest: The Pathfinder's Toll

**Giver:** Guildmaster Thorne, a scarred veteran who values preparation over bravery, often seen calculating supply lines.
**Prerequisite:** Rank F, Level 3

## Dialogue (Start)
*Guildmaster Thorne slams a ledger onto his desk, a heavy scowl etched across his scarred face. He glances at you, assessing your worth.*

**Thorne:** "You're eager. That's usually the first thing that gets a rookie killed out there. The Guild is expanding its reach. We can't rely on manual patrols forever. We need an Expeditionary force."
**Player:** "I'm ready to lead an expedition."
**Thorne:** (snorts) "Ready? You don't even know what to pack. Out there, without the Guild's immediate support, your supplies are your lifeblood. I'm not sending you into the deep wilds until you prove you understand the toll the path takes."
**Player Option A:** "I understand. What do I need to do?" (Accepts quest)
**Player Option B:** "Sounds like too much paperwork. I prefer fighting." (Refuses, can return later)

## Objectives
1. Complete a **30-minute Auto-Adventure** in any location to prove you can survive off the grid.
2. Ensure you allocate at least **1 Hardtack (Rations)** and **1 Pitch Torch** before departing to prove your preparation.
3. Return to Thorne.
   - *During the adventure, an automatic event triggers: you discover a fallen, unprepared scout.*

## Narrative Elements
- **Hook:** The introduction of the new Expeditionary force and Thorne's harsh, pragmatic reality of survival.
- **Rising Action:** The player sets out on their first self-sustained Auto-Adventure, experiencing the tension of relying on supplies rather than manual combat.
- **Climax:** The player stumbles upon the remains of a previous, less prepared scout, clutching an empty satchel. They must make a grim choice about the scout's remaining emergency supplies.

## Dialogue (Mid‑Quest – The Discovery)
*The thick undergrowth parts to reveal a grim sight: the remains of a Guild scout, their uniform torn and their rations long exhausted. Clutched in their stiff hand is an emergency satchel.*

**Player Option A (Honorable):** Leave the supplies and bring the intact satchel back to Thorne to identify the fallen.
**Player Option B (Pragmatic):** Loot the satchel for its remaining supplies (2 Potions, 1 Hardtack) and leave the rest to rot. The dead don't need rations.

## Dialogue (Resolution)
*You return to the Guild Hall and place your report—and the satchel—on Thorne's desk.*

*[If player chose Option A (Honorable)]*
**Thorne:** *He traces the Guild insignia on the satchel, his expression unreadable for a long moment.* "Scout Vane. He was... careless. But he deserved to be remembered. You did right by him, rookie. The path takes its toll, but we don't have to lose our humanity to survive it."

*[If player chose Option B (Pragmatic)]*
**Thorne:** *He inspects your gear, noting the extra supplies.* "You survived, but I see you came back heavier than you left. Found some unfortunate soul's stash, did you? The wilds belong to the living, I suppose. Just remember: one day, it might be your satchel someone else is looting."

## Resolution Consequences
**Thorne:** "You've proven you can plan for the worst. The Expeditionary force could use someone who understands the stakes. We're authorizing you for longer deployments." (hands you a weathered compass or extra supplies depending on choice)

## Rewards
- **Completion:** 500 EXP, Title "Expeditionary", unlocks 2-hour Auto-Adventures.
- **Choice A (Honorable):** +10 Guild Reputation, 1x Scout's Compass (Trinket).
- **Choice B (Pragmatic):** 2x Minor Healing Potion, 1x Hardtack.

## Agent Coordination
- **GameForge:** Implement the quest objectives requiring a 30m Auto-Adventure completion and supply allocation checks.
- **StoryWeaver:** Ensure the mission report text for this specific quest adventure reflects the grim discovery of the fallen scout.
- **Equipper:** Ensure the "Scout's Compass" trinket is added or mapped to an existing equivalent reward.
- **Foreman:** This fulfills the narrative integration for the Auto-Adventure system overhaul.
- **BugHunter:** Test the branching choice logic to ensure the correct rewards are granted.