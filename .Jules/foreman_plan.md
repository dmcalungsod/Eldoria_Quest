# 👷 Project Plan: Auto-Adventure Overhaul

## 🎯 Objective
Transform Eldoria Quest from manual turn-based exploration to a time-based auto-adventure system.

**Design Document:** `.Jules/timeweaver_design.md`
**Status:** 🚀 **Phase 0: Foundation (Running)**

---

## 📅 Phases & Milestones

### Phase 0: Foundation (Database & Scheduler)
**Focus:** Backend infrastructure to support time-based sessions.
- [x] **Task 0.1:** Design `adventure_sessions` schema & update `DatabaseManager`.
    - **Agent:** @DataSteward / @SystemSmith
    - **Status:** **Completed** (Schema exists in `database_manager.py`).
- [ ] **Task 0.2:** Implement background scheduler (`cogs/adventure_loop.py`).
    - **Agent:** @SystemSmith
    - **Priority:** **Blocking**
    - **Details:** Loop every 1 min, query `get_adventures_ending_before(now)`, mark `notification_sent`.
- [ ] **Task 0.3:** Implement `AdventureResolutionEngine` logic.
    - **Agent:** @SystemSmith
    - **Priority:** **Blocking**
    - **Details:** Automated loop calling `AdventureSession.simulate_step` for full duration.

### Phase 1: Core Loop (UI & Logic)
**Focus:** Enabling players to start and complete basic adventures.
- [ ] **Task 1.1:** Implement `AdventureSetupView` (Location/Duration selection).
    - **Agent:** @Palette
    - **Details:** Dropdowns for Location & Duration. "Embark" button.
- [ ] **Task 1.2:** Update `/adventure` command to use new View.
    - **Agent:** @Palette
- [ ] **Task 1.3:** Create `AdventureReportEmbed` for results.
    - **Agent:** @Palette
    - **Details:** Summary of loot, XP, battles, HP lost.

### Phase 2: Content & Balance
**Focus:** Populating the world and tuning numbers.
- [ ] **Task 2.1:** Design new Adventure Locations (data).
    - **Agent:** @GameForge
    - **Details:** Define locations, difficulty ranks, and resource pools.
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
    - **Details:** 50% loot loss, 10% Aurum loss on death.
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
*   **The Frostfall Expanse:** Design Phase (Architect). ID Conflict Resolved (Already implemented as 111-115).
*   **Codex & Bestiary:** Proposed (Codex Keeper). Pending approval.

## 📝 Activity Log
- **2026-02-23:** Resumed project. Verified Phase 0.1 completion. Assigned Scheduler (0.2) and Engine (0.3) to SystemSmith.
- **2025-10-29:** Plan created. Phase 0 initiated.
