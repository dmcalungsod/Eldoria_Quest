# Quest Design: The Clockwork Heart

**Designer:** Questweaver
**Status:** Draft
**Target Rank:** B (Level 22+)
**Location:** The Clockwork Halls

## Overview
A narrative-focused questline exploring the unintended consequences of Veil corruption on ancient machinery. It challenges the player to decide between pragmatism (security) and empathy (potential life), with lasting consequences for the Clockwork Halls' atmosphere.

---

## Quest 1: The Clockwork Heart - Anomaly
**Quest Giver:** Artificer Jolen (Entrance to Clockwork Halls)
**Prerequisites:** Rank B, Completion of "Gears of War" (Quest ID 64)

### Narrative Hook
Artificer Jolen is puzzled. His scanners have picked up a signal from a Brass Golem that isn't following the standard patrol algorithms. Instead of hunting intruders, it appears to be... waiting.

### Dialogue Script (Start)
**Jolen:** "Ah, you're back. Good timing. My sensors are picking up a rogue signal in Sector 4. It's a Brass Golem, Unit 734. But it's not attacking miners or repairing vents. It's just standing there, near the old cooling intake. And its core signature... it's fluctuating in a rhythm. Like a heartbeat. I need you to get eyes on it. If it's malfunctioning, it could blow the whole sector."

### Objectives
1.  **Locate: Unit 734**
    *   *Context:* Deep in the Clockwork Halls, in a surprisingly quiet alcove.
    *   *Flavor Text:* "You find the golem standing motionless. In its massive metal hands, it cradles a small, oil-stained flower growing from a crack in the floor."
2.  **Defeat: Scavenger Constructs**
    *   *Context:* Other machines see Unit 734 as vulnerable/defective and are moving to recycle it.
    *   *Flavor Text:* "Scavenger spiders descend from the ceiling, their sensors locked on the motionless golem. You must intervene."
3.  **Scan: Unit 734**
    *   *Context:* Use Jolen's scanner on the golem.
    *   *Flavor Text:* "The scanner hums. The golem doesn't resist. It simply tilts its head, its optic lens focusing on you with a strange, flickering curiosity."

### Dialogue Script (End)
**Jolen:** "You're back. Let me see the data... incredible. The corruption didn't just break its targeting logic; it rewrote it. It's prioritizing 'preservation' over 'elimination'. But there's a problem. Its core is unstable. The new code is drawing too much power. It's going to go critical."

**Rewards:**
- Experience: 2200
- Aurum: 650
- Item: "Encrypted Log Cylinder"

---

## Quest 2: The Clockwork Heart - Divergence
**Quest Giver:** Artificer Jolen
**Prerequisites:** Completion of "The Clockwork Heart - Anomaly"

### Narrative Hook
The player must decide the fate of Unit 734. Jolen presents the dilemma: the golem is dangerous but unique.

### Dialogue Script (The Choice)
**Jolen:** "Here's the situation. Unit 734 is a ticking time bomb.
Option A: We **dismantle it**. I can use its parts to reinforce the main lift. It's safe, practical, and we get high-grade salvage.
Option B: We try to **stabilize it**. I can write a patch to regulate its power draw, but you'll have to install it while it's active. If it panics, it might crush you. And even if it works, we're leaving a sentient 3-ton war machine roaming the halls.
What's the call, adventurer?"

### Path A: The Pragmatist (Dismantle)
**Player Choice:** "It's too dangerous. Dismantle it."
**Objective:**
1.  **Defeat: Unit 734**
    *   *Flavor Text:* "The golem raises its arms, not to strike, but to shield the flower. As it falls, the light in its eyes fades slowly, resigned."
2.  **Retrieve: Pristine Gear Heart**
**Reward:**
- Experience: 2500
- Aurum: 800
- Item: **"Artificer's Alloy"** (High-value crafting material)
- Title: **"The Realist"**

### Path B: The Idealist (Stabilize)
**Player Choice:** "It deserves a chance. I'll install the patch."
**Objective:**
1.  **Defend: Unit 734**
    *   *Context:* While the patch uploads, the golem's distress signal attracts a wave of elites.
    *   *Flavor Text:* "The golem shudders as the code rewrites its core. You hold back the tide of Automaton Knights until the process completes."
2.  **Interact: Unit 734**
    *   *Flavor Text:* "Unit 734 stabilizes. It offers you a single, perfect metal gear, then returns to guarding its flower."
**Reward:**
- Experience: 2500
- Aurum: 500 (Less gold)
- Item: **"Heart of the Machine"** (Unique trinket: +Crit Chance or similar effect)
- Title: **"Iron Soul"**
- *Lore Consequence:* Unit 734 becomes a permanent rare spawn NPC that grants a small buff to players nearby.

---

## 🤝 Agent Coordination
*   **GameForge:** Need to implement the branching quest logic or two separate follow-up quests ("Dismantle" vs "Stabilize"). Requires a "Defend" objective type or a "Survive for X turns" mechanic.
*   **StoryWeaver:** Review dialogue for voice and tone. Jolen should sound torn between his scientific curiosity and his duty to safety.
*   **Tactician:** Balance the "Defend" encounter. It needs to be challenging to justify the "Hard Way" choice.
*   **Namewright:** Confirm "Unit 734" designation or suggest a better one.
*   **ChronicleKeeper:** Add achievement "Ghost in the Machine" for completing either path.

## 🚧 Boundaries Check
*   **Mechanics:** Uses existing "Defeat", "Retrieve", "Interact" objectives. The "Defend" scenario can be simulated by killing a set number of enemies that spawn at the location.
*   **World State:** Path B implies a persistent NPC. If dynamic world state isn't possible, the golem can just be part of the flavor text or a rare spawn added to `adventure_locations.py` with a 0% aggression rate (if supported).
