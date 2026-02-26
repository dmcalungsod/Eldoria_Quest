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
    - **Subtask 2.2a:** Nerf "Deepgrove Roots" (Move `Feral Stag` to conditional, restrict drops). [x] **Completed** (Fixed by Equilibrium)
    - **Subtask 2.2b:** Buff "The Shrouded Fen" (Better mid-game drops).
    - **Subtask 2.2c:** Buff "The Void Sanctum" & "Clockwork Halls" (End-game incentives).
    - **Due:** 2026-03-06
- [ ] **Task 2.3:** Implement Fatigue System (>4h risk increase).
    - **Agent:** @GameBalancer / @SystemSmith
    - **Details:** Modify `AdventureResolutionEngine` to increase monster damage scaling for long durations.
    - **Due:** 2026-03-05
- [x] **Task 2.4:** Implement "Frostfall Expedition" Event.
    - **Agent:** @EventHerald
    - **Status:** **Completed** (Event active with loot bonuses).

### Phase 3: Integration & Polish
**Focus:** Flavor, depth, and safety nets.
- [x] **Task 3.1:** Implement Death Penalty logic.
    - **Agent:** @Grimwarden
    - **Status:** **Completed** (10% Aurum / 50% Material loss implemented in `adventure_manager.py`).
- [x] **Task 3.2:** Write Flavor Text for Adventure Reports.
    - **Agent:** @StoryWeaver
    - **Status:** **Completed** (`narrative_data.py` populated with location/outcome flavor).
- [ ] **Task 3.3:** Implement Travel Supplies.
    - **Agent:** @Equipper / @SystemSmith
    - **Details:** Create items (Hardtack, Pitch Torch, etc.), add UI selector in `AdventureSetupView`, implement usage logic.
    - **Status:** **In Progress** (Names provided by Namewright).
    - **Due:** 2026-03-07

### Phase 4: Testing & Launch
**Focus:** Stress testing and final verification.
- [ ] **Task 4.1:** Stress test Scheduler (10k simulated sessions).
    - **Agent:** @BugHunter
- [ ] **Task 4.2:** Verify "Cancel" exploit prevention.
    - **Agent:** @BugHunter

---

## 🛠️ Phase 5: Tech Debt & Maintenance (New)
**Focus:** Resolving critical issues identified by Issue Crafter.
- [ ] **Task 5.1:** Fix Critical `pip` Vulnerability (CVE-2026-1703).
    - **Agent:** @Sentinel
    - **Reference:** Issue #10
    - **Due:** **IMMEDIATE**
- [ ] **Task 5.2:** Refactor High-Complexity Methods.
    - **Agent:** @SystemSmith
    - **Subtask 5.2a:** `CombatEngine.run_combat_turn` (Issue #11)
    - **Subtask 5.2b:** `AdventureEvents.regeneration` (Issue #12)
    - **Subtask 5.2c:** `AdventureSession.simulate_step` (Issue #13)
    - **Due:** 2026-03-10

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
**Status:** **Design/Implementation**
- [x] **Task W.1:** Design Skill Tree Titles.
    - **Agent:** @Namewright / @ChronicleKeeper
    - **Status:** **Completed** (Ironclad, Reaver, Titan).
- [ ] **Task W.2:** Implement Skill Logic (Juggernaut vs Berserker).
    - **Agent:** @GameForge / @Tactician
    - **Reference:** Issue #9
    - **Due:** 2026-03-10

---

## 📝 Activity Log
- **2026-03-04:** Added Warrior Skill Tree project. Updated Phase 5 with Issue IDs. Marked Task 2.2a (Deepgrove) and 2.4 (Frostfall Event) as Completed.
- **2026-02-25 (Update):** Integrated Analyst findings (Task 2.2 split), Namewright updates (Task 3.3/Alchemist), and Issue Crafter reports (Phase 5). Marked Tasks 2.1 and 3.2 as Complete.
- **2026-02-26:** Confirmed Phase 1 (UI) and key Phase 2/3 tasks (Locations, Death Penalty, Flavor Text) are Complete. Updated plan to reflect rapid progress. Assigned remaining Fatigue and Supply tasks.
- **2026-02-25:** Phase 0 (Backend) marked Complete. Phase 1 detailed tasks assigned to @Palette and @SystemSmith.
- **2026-02-24:** Updated plan. Marked Task 0.1 and 2.1 as Complete. Re-assigned blocking Tasks 0.2 and 0.3 to SystemSmith.
- **2026-02-23:** Resumed project. Verified Phase 0.1 completion. Assigned Scheduler (0.2) and Engine (0.3) to SystemSmith.
- **2025-10-29:** Plan created. Phase 0 initiated.
