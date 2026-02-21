# 👷 Project Plan: Auto-Adventure Overhaul

## 🎯 Objective
Transform Eldoria Quest from manual turn-based exploration to a time-based auto-adventure system.

**Design Document:** `.Jules/timeweaver_design.md`
**Status:** 🚀 **Phase 0: Foundation (Starting)**

---

## 📅 Phases & Milestones

### Phase 0: Foundation (Database & Scheduler)
**Focus:** Backend infrastructure to support time-based sessions.
- [ ] **Task 0.1:** Design `adventure_sessions` schema & update `DatabaseManager`.
    - **Agent:** @DataSteward / @SystemSmith
    - **Details:** Add `start_time`, `end_time`, `duration_minutes`, `location_id`, `active`, `supplies`.
- [ ] **Task 0.2:** Implement background scheduler (`cogs/adventure_loop.py`).
    - **Agent:** @SystemSmith
    - **Details:** Loop every 1 min, query `get_adventures_ending_before(now)`, mark `notification_sent`.
- [ ] **Task 0.3:** Create basic `AdventureResolutionEngine` structure (stub).
    - **Agent:** @SystemSmith
    - **Details:** Class with `calculate_step(player, location)` method structure.

### Phase 1: Core Loop (UI & Logic)
**Focus:** Enabling players to start and complete basic adventures.
- [ ] **Task 1.1:** Implement `AdventureSetupView` (Location/Duration selection).
    - **Agent:** @Palette
    - **Details:** Dropdowns for Location & Duration. "Embark" button.
- [ ] **Task 1.2:** Update `/adventure` command to use new View.
    - **Agent:** @Palette
- [ ] **Task 1.3:** Implement `AdventureResolutionEngine` logic.
    - **Agent:** @SystemSmith / @Tactician
    - **Details:** Step-by-step simulation (Combat/Gather/Event rolls).
- [ ] **Task 1.4:** Create `AdventureReportEmbed` for results.
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

## 📝 Activity Log
- **2025-10-29:** Plan created. Phase 0 initiated.
