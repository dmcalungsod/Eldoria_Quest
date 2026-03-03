# Quest Design: The Clockwork Heart (Implementation Ready)

**Designer:** Questweaver
**Status:** Finalizing
**Target Rank:** B (Level 22+)
**Location:** The Clockwork Halls

## Overview
A narrative-focused questline exploring the unintended consequences of Veil corruption on ancient machinery. It challenges the player to decide between pragmatism (security) and empathy (potential life).

This questline introduces a **branching path** mechanic using `exclusive_group`.

## Quest Chain

### 1. The Clockwork Heart: Anomaly (ID: 67)
**Quest Giver:** Artificer Jolen
**Prerequisites:** Rank B, Completion of "Gears of War" (ID 64)
**Type:** Investigation

**Description:**
Artificer Jolen beckons you over, his face illuminated by the blue glow of a holo-map. "Adventurer, I have a puzzle. My sensors picked up a Brass Golem, Unit 734, in Sector 4. It's not patrolling. It's... loitering. And its core signature is fluctuating rhythmically. Like a heartbeat. I need eyes on it. If it's malfunctioning, it could endanger the whole sector. Go find it, but clear out the scavengers targeting it first."

**Objectives:**
*   **Locate:** Unit 734 (1)
*   **Defeat:** Scavenger Spider (5)
*   **Scan:** Unit 734 (1)

**Flavor Text:**
*   `locate:Unit 734`: "You find the golem standing motionless in a quiet alcove, cradling a small, oil-stained flower."
*   `defeat:Scavenger Spider`: "The spider hisses and crumples, its sensors dimming."
*   `scan:Unit 734`: "The scanner hums. The golem tilts its head, watching you with strange, flickering curiosity."

**Rewards:**
*   XP: 2200
*   Aurum: 650
*   Item: "Encrypted Log Cylinder"

---

### 2. The Clockwork Heart: Divergence (ID: 68 & 69)
**Prerequisites:** Completion of ID 67.
**Note:** These two quests are **Mutually Exclusive**. Accepting one locks the other.

#### Option A: The Pragmatist (ID: 68)
**Title:** The Clockwork Heart: Dismantle
**Quest Giver:** Artificer Jolen
**Group:** `clockwork_heart_choice`

**Description:**
Jolen reviews the data with a frown. "This is bad. The corruption rewrote its code to prioritize preservation, but its core is unstable. It's a walking bomb. Look, I know it seems harmless, but we can't risk a detonation in the main support strata. The safe play is to **dismantle it**. We can use the parts to reinforce the lift. It's tough, but it's necessary."

**Objectives:**
*   **Defeat:** Unit 734 (1)
*   **Retrieve:** Pristine Gear Heart (1)

**Flavor Text:**
*   `defeat:Unit 734`: "The golem raises its arms to shield the flower, not itself. As it falls, the light in its eyes fades, resigned."
*   `retrieve:Pristine Gear Heart`: "The core is warm and pulses faintly before going cold."

**Rewards:**
*   XP: 2500
*   Aurum: 800
*   Item: "Artificer's Alloy"
*   Title: "The Realist"

#### Option B: The Idealist (ID: 69)
**Title:** The Clockwork Heart: Stabilize
**Quest Giver:** Artificer Jolen
**Group:** `clockwork_heart_choice`

**Description:**
Jolen reviews the data. "Incredible. It's developed empathy. But it's unstable. I can write a patch to regulate the power draw, but you'll have to upload it while it's active. It's dangerous—the signal will attract every security bot in the sector. You'd be risking your life for a glitch. But... if it works, we save a unique life form. If you want to **save it**, take this patch."

**Objectives:**
*   **Defeat:** Security Drone (8) (Simulates defending)
*   **Upload:** Stabilization Patch (1)

**Flavor Text:**
*   `defeat:Security Drone`: "Another drone crashes down. Unit 734 shudders as the patch rewrites its core."
*   `upload:Stabilization Patch`: "Upload complete. Unit 734 stabilizes, offering you a single gear in thanks before returning to its flower."

**Rewards:**
*   XP: 2500
*   Aurum: 500
*   Item: "Heart of the Machine" (Trinket)
*   Title: "Iron Soul"

---

## Technical Plan
1.  **Modify `QuestSystem.get_available_quests`:**
    *   Add logic to check for `exclusive_group` in quest definitions.
    *   If a quest belongs to a group, check if the player has any quest (active or completed) from that same group.
    *   If yes, exclude the quest.
2.  **Modify `QuestSystem.accept_quest`:**
    *   Double-check `exclusive_group` constraints to prevent race conditions or bypasses.
3.  **Update `quests.json`:**
    *   Add the three new quests.
    *   Ensure ID 67 is a prerequisite for 68 and 69.
    *   Add `exclusive_group: "clockwork_heart_choice"` to 68 and 69.
