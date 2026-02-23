# 👷 Project Plan: Auto-Adventure Overhaul

## 🎯 Objective
Transform Eldoria Quest from manual turn-based exploration to a time-based auto-adventure system.

**Design Document:** `.Jules/timeweaver_design.md`
**Status:** 🚧 **Phase 1: Core Loop (UI & Interaction)**

---

## 📅 Phases & Milestones

### Phase 0: Foundation (Database & Scheduler)
**Focus:** Backend infrastructure to support time-based sessions.
- [x] **Task 0.1:** Design `adventure_sessions` schema & update `DatabaseManager`.
    - **Agent:** @DataSteward / @SystemSmith
    - **Status:** **Completed** (Schema exists in `database_manager.py`).
- [x] **Task 0.2:** Implement background scheduler (`cogs/adventure_loop.py`).
    - **Agent:** @SystemSmith
    - **Status:** **Completed** (`AdventureLoop` implemented).
- [x] **Task 0.3:** Implement `AdventureResolutionEngine` logic.
    - **Agent:** @SystemSmith
    - **Status:** **Completed** (`AdventureResolutionEngine` implemented).
- [x] **Task 0.4:** Update `AdventureSession` to support "Background Simulation" mode.
    - **Agent:** @SystemSmith
    - **Status:** **Completed** (`simulate_step(background=True)` implemented).

### Phase 1: Core Loop (UI & Interaction)
**Focus:** Enabling players to start, track, and complete adventures.
- [ ] **Task 1.1:** Update `AdventureSetupView` (Duration Selection).
    - **Agent:** @Palette
    - **File:** `game_systems/adventure/ui/setup_view.py`
    - **Details:** Add dropdown for Duration [30m, 1h, 4h, 8h]. Pass duration to `manager.start_adventure`.
- [ ] **Task 1.2:** Update `AdventureView` Logic (Start/Resume Handling).
    - **Agent:** @Palette / @SystemSmith
    - **File:** `game_systems/character/ui/adventure_menu.py`
    - **Details:**
        - Check `session["status"]`.
        - If `completed`: Call `manager.end_adventure` and show Rewards.
        - If `in_progress`: Show Status Embed (Location, Time Remaining).
        - If `failed`: Show Failure Report (if applicable).
- [ ] **Task 1.3:** Create "Adventure Status" Embed/View.
    - **Agent:** @Palette
    - **File:** `game_systems/adventure/ui/adventure_embeds.py` (Embed), `game_systems/adventure/ui/status_view.py` (New View).
    - **Details:** Embed showing Location, Duration, Elapsed Time, Expected Return. Include "Retreat" button.
- [ ] **Task 1.4:** Update `AdventureEmbeds` for Completion Report.
    - **Agent:** @Palette
    - **File:** `game_systems/adventure/ui/adventure_embeds.py`
    - **Details:** Update `build_summary_embed` or create `build_adventure_report` to include "Steps", "Battles", "Harvests".

### Phase 2: Content & Balance
**Focus:** Populating the world and tuning numbers.
- [x] **Task 2.1:** Design new Adventure Locations (data).
    - **Agent:** @GameForge
    - **Status:** **Completed** (Verified `adventure_locations.py` contains 12+ locations including Frostfall Expanse).
- [ ] **Task 2.2:** Configure Loot Tables & Drop Rates.
    - **Agent:** @DataSteward / @GameBalancer
    - **Details:** Ensure economy balance (materials vs time).
- [ ] **Task 2.3:** Tune Risk/Reward (Fatigue, Night penalty).
    - **Agent:** @GameBalancer
    - **Details:** Adjust monster damage scaling and "Rescue" mechanics.

### Phase 3: Integration & Polish
**Focus:** Flavor, depth, and safety nets.
- [ ] **Task 3.1:** Implement Death Penalty & "Rescue" logic.
    - **Agent:** @Grimwarden
    - **Details:** 50% loot loss, 10% Aurum loss on death (Partially implemented in `adventure_manager.py`).
- [ ] **Task 3.2:** Write Flavor Text for Adventure Reports.
    - **Agent:** @StoryWeaver
    - **Details:** Dynamic descriptions based on events.
- [ ] **Task 3.3:** Add "Travel Supplies" (Rations, Torches).
    - **Agent:** @Equipper / @DataSteward

### Phase 4: Testing & Launch
**Focus:** Stress testing and final verification.
- [ ] **Task 4.1:** Stress test Scheduler (10k simulated sessions).
    - **Agent:** @BugHunter
- [ ] **Task 4.2:** Verify "Cancel" exploit prevention.
    - **Agent:** @BugHunter

---

## 🏗️ Parallel Projects
*   **The Alchemist Class:** Design Phase (Namewright). Pending ID coordination.
*   **The Frostfall Expanse:** Implemented in `adventure_locations.py` (IDs 111-115).
*   **Codex & Bestiary:** Proposed (Codex Keeper). Pending approval.

## 📝 Activity Log
- **2026-02-25:** Phase 0 (Backend) marked Complete. Phase 1 detailed tasks assigned to @Palette and @SystemSmith.
- **2026-02-24:** Updated plan. Marked Task 0.1 and 2.1 as Complete. Re-assigned blocking Tasks 0.2 and 0.3 to SystemSmith.
- **2026-02-23:** Resumed project. Verified Phase 0.1 completion. Assigned Scheduler (0.2) and Engine (0.3) to SystemSmith.
- **2025-10-29:** Plan created. Phase 0 initiated.
