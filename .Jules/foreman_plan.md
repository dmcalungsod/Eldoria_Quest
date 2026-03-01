# 👷 Project Plan: Auto-Adventure Overhaul

## 🎯 Objective
Transform Eldoria Quest from manual turn-based exploration to a time-based auto-adventure system.

**Design Document:** `.Jules/timeweaver_design.md`
**Status:** 🚧 **Phase 2: Content & Balance**

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
- [x] **Task 1.1:** Update `AdventureSetupView` (Duration Selection).
    - **Agent:** @Palette
    - **File:** `game_systems/adventure/ui/setup_view.py`
    - **Status:** **Completed** (Duration selector implemented).
- [x] **Task 1.2:** Update `AdventureView` Logic (Start/Resume Handling).
    - **Agent:** @Palette / @SystemSmith
    - **File:** `game_systems/character/ui/adventure_menu.py`
    - **Status:** **Completed** (Integration verified).
- [x] **Task 1.3:** Create "Adventure Status" Embed/View.
    - **Agent:** @Palette
    - **File:** `game_systems/adventure/ui/status_view.py`
    - **Status:** **Completed** (Status view with Refresh/Retreat implemented).
- [x] **Task 1.4:** Update `AdventureEmbeds` for Completion Report.
    - **Agent:** @Palette
    - **File:** `game_systems/adventure/ui/adventure_embeds.py`
    - **Status:** **Completed** (`build_summary_embed` implemented).

### Phase 2: Content & Balance
**Focus:** Populating the world and tuning numbers.
- [x] **Task 2.1:** Design new Adventure Locations (data).
    - **Agent:** @GameForge
    - **Status:** **Completed** (Verified `adventure_locations.py` contains 12+ locations including Frostfall Expanse).
- [ ] **Task 2.2:** Configure Loot Tables & Drop Rates (Economy Fixes).
    - **Agent:** @GameBalancer
    - **Subtask 2.2a:** Nerf "Deepgrove Roots" (Move `Feral Stag` to conditional, restrict drops). **[x] Completed**
    - **Subtask 2.2b:** Buff "The Shrouded Fen" (Better mid-game drops). **[x] Completed**
    - **Subtask 2.2c (Expanded):** Buff "The Void Sanctum" & "Clockwork Halls" (End-game incentives). **[ ] In Progress**
    - **Subtask 2.2d:** Tune "Thunder-Crag Coast" & "Shimmering Wastes" (Underperforming rewards). **[x] Completed**
    - **Due:** 2026-03-08
- [x] **Task 2.3:** Implement Fatigue System (>4h risk increase).
    - **Agent:** @GameBalancer / @SystemSmith
    - **Details:** Modify `AdventureSession` to increase monster damage scaling for long durations.
    - **Status:** **Completed** (Verified `_calculate_fatigue_multiplier` in `adventure_session.py`).
- [x] **Task 2.4:** Resolve Rank Logic Conflict (Frostfall vs Archipelago).
    - **Agent:** @GameBalancer / @GameForge
    - **Details:** Resolve Level 25/28 vs Rank A/B inconsistency.
    - **Due:** 2026-03-08

### Phase 3: Integration & Polish
**Focus:** Flavor, depth, and safety nets.
- [x] **Task 3.1:** Implement Death Penalty logic.
    - **Agent:** @Grimwarden
    - **Status:** **Completed** (10% Aurum / 50% Material loss implemented in `adventure_manager.py`).
- [x] **Task 3.2:** Write Flavor Text for Adventure Reports.
    - **Agent:** @StoryWeaver
    - **Status:** **Completed** (`narrative_data.py` populated with location/outcome flavor).
- [x] **Task 3.3:** Implement Travel Supplies.
    - **Agent:** @Equipper / @SystemSmith
    - **Status:** **Completed** (Verified `hardtack`/`pitch_torch` in `consumables.json`, logic in `adventure_session.py`).

### Phase 4: Testing & Launch
**Focus:** Stress testing and final verification.
- [x] **Task 4.1:** Stress test Scheduler (10k simulated sessions).
    - **Agent:** @BugHunter
- [x] **Task 4.2:** Verify "Cancel" exploit prevention.
    - **Agent:** @BugHunter

---

## 📌 Tracked Issues
**Focus:** Addressing issues reported by Issue Crafter.
- [ ] **Issue #1:** [Feature] Auto-Adventure: Loot Table & Drop Rate Tuning
    - **Agent:** @DataSteward, @GameBalancer
- [ ] **Issue #2:** [Feature] Auto-Adventure: Fatigue System
    - **Agent:** @GameBalancer
- [ ] **Issue #3:** [Feature] Auto-Adventure: Travel Supplies (Rations & Torches)
    - **Agent:** @Equipper
- [ ] **Issue #4:** [Test] Auto-Adventure: Stress Test Scheduler
    - **Agent:** @BugHunter
- [ ] **Issue #5:** [Test] Auto-Adventure: Exploit Verification
    - **Agent:** @BugHunter
- [ ] **Issue #6:** [Feature] The Eldoria Codex System
    - **Agent:** @CodexKeeper
- [ ] **Issue #7:** [Feature] Alchemist Class Implementation
    - **Agent:** @Namewright, @GameForge
- [ ] **Issue #8:** [UX] Implement One UI Policy
    - **Agent:** @Palette

---

## 🛠️ Phase 5: Tech Debt & Maintenance (New)
**Focus:** Resolving critical issues identified by Issue Crafter.
- [ ] **Task 5.1:** Fix Critical `pip` Vulnerability (CVE-2026-1703).
    - **Agent:** @Sentinel
    - **Due:** **IMMEDIATE (CRITICAL)**
- [ ] **Task 5.2:** Refactor High-Complexity Methods.
    - **Agent:** @SystemSmith
    - **Subtask 5.2a:** `CombatEngine.run_combat_turn`
    - **Subtask 5.2b:** `AdventureEvents.regeneration`
    - **Subtask 5.2c:** `AdventureSession.simulate_step`
    - **Due:** 2026-03-10
- [x] **Task 5.3:** Update Grey Ward Faction (Issue #17).
    - **Agent:** @GameForge
    - **Details:** Update `factions.py` to match Namewright's design.
    - **Due:** 2026-03-08
- [ ] **Task 5.4:** Add Alchemist Materials (Issue #18).
    - **Agent:** @DataSteward
    - **Details:** Add `primordial_ooze`, `brimstone`, `lunawort` to `materials.py`.
    - **Due:** 2026-03-08

---

## 🏗️ Parallel Projects

### The Alchemist Class (New)
**Design:** `.Jules/architect_designs/class_alchemist.md`
**Status:** **Implementation Phase**
- [ ] **Task A.1:** Create Alchemist Skills (Vitriol Bomb, Triage, etc.).
    - **Agent:** @GameForge / @Tactician
    - **Due:** 2026-03-08
- [ ] **Task A.2:** Create Alchemist Equipment & Items.
    - **Agent:** @Equipper
    - **Due:** 2026-03-08
- [ ] **Task A.3:** Update Character Creation/Job Selection.
    - **Agent:** @GameForge
    - **Due:** 2026-03-09

### Warrior Skill Tree Expansion (New)
**Design:** `.Jules/architect_designs/skill_tree_warrior.md`
**Status:** **Implementation Phase**
- [ ] **Task W.1:** Implement Recoil/Lifesteal mechanics.
    - **Agent:** @Tactician
    - **Due:** 2026-03-10
- [ ] **Task W.2:** Add 7 new Warrior skills.
    - **Agent:** @GameForge
    - **Due:** 2026-03-10

### Rogue Skill Tree Expansion (New)
**Design:** `.Jules/architect_designs/skill_tree_rogue.md`
**Status:** **Design Approved / Implementation Phase**
- [ ] **Task R.1:** Implement Mechanics (`next_hit_crit`, `conditional_multiplier`).
    - **Agent:** @Tactician
    - **Due:** 2026-03-10
- [ ] **Task R.2:** Implement Rogue Skills (`Shadow Step`, `Venomous Strike`, etc.).
    - **Agent:** @GameForge
    - **Due:** 2026-03-10
- [ ] **Task R.3:** Create Rogue Achievements.
    - **Agent:** @ChronicleKeeper
    - **Due:** 2026-03-10

---

## 📝 Activity Log
- **2026-02-27:** Verified Task 3.3 (Supplies) as Complete. Added Rogue Skill Tree project and Analyst Integration tasks (2.2c/d, 2.4). Flagged Task 5.1 as CRITICAL.
- **2026-02-25 (Update):** Integrated Analyst findings (Task 2.2 split), Namewright updates (Task 3.3/Alchemist), and Issue Crafter reports (Phase 5). Marked Tasks 2.1 and 3.2 as Complete.
- **2026-02-26:** Confirmed Phase 1 (UI) and key Phase 2/3 tasks (Locations, Death Penalty, Flavor Text) are Complete. Updated plan to reflect rapid progress. Assigned remaining Fatigue and Supply tasks.
- **2026-02-25:** Phase 0 (Backend) marked Complete. Phase 1 detailed tasks assigned to @Palette and @SystemSmith.
- **2026-02-24:** Updated plan. Marked Task 0.1 and 2.1 as Complete. Re-assigned blocking Tasks 0.2 and 0.3 to SystemSmith.
- **2026-02-23:** Resumed project. Verified Phase 0.1 completion. Assigned Scheduler (0.2) and Engine (0.3) to SystemSmith.
- **2025-10-29:** Plan created. Phase 0 initiated.
