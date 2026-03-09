# Quest Design: The Drowned Salvage

**Designer:** Questweaver
**Status:** Ready for Implementation
**Target Rank:** A (Level 30+)

## Core Identity
- **Quest Name:** The Drowned Salvage
- **Giver NPC:** Captain Vane (A grizzled, one-eyed leader of the Deep Salvagers. He's pragmatic, cynical, and wears armor patched with rusted ship plating and coral.)
- **Location:** The Drowned Courtyard (The Sunken Grotto)
- **Prerequisites:** Rank A, must have access to The Sunken Grotto and an `Abyssal Rebreather`.

## Narrative Elements
- **Hook:** Captain Vane and his Deep Salvagers have found the motherlode: an intact vault in the Whispering Caverns belonging to a pre-Sundering noble house. However, the combination mechanism is rusted shut, and the only way to dissolve the rust without destroying the contents is with the concentrated acid of a Coral-Bound Goliath.
- **Rising Action:** The player must dive deeper into the Grotto to hunt these heavily armored beasts. The dive is complicated by the oppressive environment, the ever-draining oxygen, and the looming threat of the Leviathan's Shadow.
- **Climax:** A two-part challenge: First, tracking down and defeating a Coral-Bound Goliath to harvest its acidic gland. Second, returning to the vault and making a moral choice about the recovered wealth.
- **Resolution:** A difficult choice upon opening the vault. The player discovers that the vault contains not just wealth, but ancient navigational charts detailing safe routes through the treacherous Archipelago currents—information the Guild desperately needs for expansion.

## Dialogue Script

### Start
*Captain Vane spits a glob of dark, briny tobacco onto the wet stone. He looks you up and down, his single eye lingering on your Abyssal Rebreather.*

**Vane:** "You've got the lungs for the deep, eh? Good. My crew found a vault down in the Whispering Caverns. Solid sea-iron, rusted tighter than a clam. We try to pry it, we crush what's inside."
**Player:** "How do you plan to open it?"
**Vane:** "We don't. You do. The Coral-Bound Goliaths further down produce an acid strong enough to melt the rust, but weak enough not to eat the iron. Bring me a Goliath's Acid Gland, and I'll give you a cut of the salvage. But be quick. The Leviathan's Shadow is restless today."
**Player Option A:** "I'll get your acid. Keep your end of the bargain." (Accepts quest)
**Player Option B:** "I'm not risking my neck for a scavenger's loot." (Refuses, can return later)

### Mid-Quest (Optional Return without items)
**Vane:** "Still breathing, I see. Where's the gland? If you're scared of a overgrown crab, say so, and I'll send one of my own."

### Climax (Upon returning with the gland and opening the vault)
*You hand over the pulsing, noxious gland. Vane carefully applies the acid to the vault's hinges. With a grinding shriek, the heavy doors swing open, revealing chests of Sunken Gold and a sealed, watertight tube.*

*Vane pries open the tube and unrolls a crackling parchment. His eye widens.*

**Vane:** "By the deep... Navigation charts. Pre-Sundering. This shows safe passages through the Archipelago that the Guild doesn't even know exist. This isn't just gold, adventurer. This is a monopoly on trade routes. We keep this quiet, the Salvagers become kings."
**Player:** "The Guild needs those charts to supply the Vanguard outposts."
**Vane:** (scowling) "The Guild left us to rot. These are mine by right of salvage. But... you did the heavy lifting. I'll buy your silence. Take the gold, leave the charts."

**Player Option A (Give to Vane):** "A deal's a deal. The salvage is yours."
**Player Option B (Take the Charts for the Guild):** "The Vanguard's survival is more important than your monopoly. I'm taking the charts."

### Resolution (Option A - Vane)
*Vane grins, exposing a row of gold teeth. He tosses you a heavy pouch of coins and a piece of rare coral.*
**Vane:** "A smart choice. You're alright for a landsman. You ever need something dragged up from the dark, you come to me."

### Resolution (Option B - Guild)
*Vane's hand drops to his rusted cutlass, but he stops, realizing he can't beat you. He spits on the ground.*
**Vane:** "Guild lapdog. Take your damn paper. But don't expect a warm welcome from the Salvagers again."

## Objectives
1.  **Objective 1:** Dive into the Whispering Caverns and locate a Coral-Bound Goliath. (Defeat 1 Coral-Bound Goliath)
2.  **Objective 2:** Harvest the acidic gland. (Collect 1 Goliath Acid Gland)
3.  **Objective 3:** Return to the vault in the Drowned Courtyard and make your choice.

## Rewards
-   **Completion:** 8500 EXP.
-   **Choice A (Vane):** +20 Deep Salvagers Reputation, 4000 Aurum, 1x Luminous Pearl, Title: "The Deep Scavenger".
-   **Choice B (Guild):** +20 Guild Reputation, -10 Deep Salvagers Reputation, 1x "Navigator's Astrolabe" (Trinket), Title: "Chart-Keeper".

## Agent Coordination
-   **GameForge:** Implement the objectives in `quests.json` and the quest item (`goliath_acid_gland`) in `quest_items.json`. Ensure `coral_bound_goliath` exists in `monsters.json`.
-   **Grimwarden:** Ensure the Oxygen Management mechanics add pressure to the hunt for the Goliath.
-   **ChronicleKeeper:** Add an achievement for securing the navigational charts for the Guild.
-   **StoryWeaver:** Review dialogue for the grizzled, nautical tone of Captain Vane.
-   **Equipper:** Ensure "Navigator's Astrolabe" is an available trinket.
