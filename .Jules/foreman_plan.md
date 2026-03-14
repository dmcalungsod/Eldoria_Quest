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
- [x] **Task 2.2:** Configure Loot Tables & Drop Rates (Economy Fixes).
    - **Agent:** @GameBalancer
    - **Subtask 2.2a:** Nerf "Deepgrove Roots" (Move `Feral Stag` to conditional, restrict drops). **[x] Completed**
    - **Subtask 2.2b:** Buff "The Shrouded Fen" (Better mid-game drops. EV target > ~350 Aurum per 30m). **[ ] Reopened**
    - **Subtask 2.2c (Expanded):** Buff "The Void Sanctum" & "Clockwork Halls" (End-game incentives. Clockwork Halls EV target > ~900 Aurum per 30m). **[ ] Reopened**
    - **Subtask 2.2d:** Tune "Thunder-Crag Coast" & "Shimmering Wastes" (Must scale past Molten Caldera's high EV 1500.50). **[ ] Reopened**
    - **Subtask 2.2e (New):** Address "Celestial Archipelago" EV (EV 624.25 < Rank B). Raise to > 1300 Aurum. **[ ] Unstarted**
- [ ] **Task 2.2f:** Address "The Silent City of Ouros" drops (EV 307.0 < Rank S). Raise significantly to be competitive with The Void Sanctum (915.8 EV/Hr). Includes adding missing monsters (`temporal_wraith`, `hollowed_sentinel`, `abyssal_creeper`) per Analyst report.
    - **Agent:** @GameForge, @GameBalancer
    - **Due:** 2026-03-15
- [x] **Task 2.3:** Implement Fatigue System (>4h risk increase).
    - **Agent:** @GameBalancer / @SystemSmith
    - **Details:** Modify `AdventureSession` to increase monster damage scaling for long durations.
    - **Status:** **Completed** (Verified `_calculate_fatigue_multiplier` in `adventure_session.py`).
- [x] **Task 2.4:** Resolve Rank Logic Conflict (Frostfall vs Archipelago).
    - **Agent:** @ProgressionBalancer
    - **Details:** Changed `min_rank` from "A" to "B" for `celestial_archipelago`.
    - **Status:** **Completed**

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
- [x] **Task 4.3:** Verify Codex unlock triggers for edge cases and duplicate entries.
    - **Agent:** @BugHunter

---

## 📌 Tracked Issues
**Focus:** Addressing issues reported by Issue Crafter.
- [ ] **Issue #1:** [Feature] Auto-Adventure: Loot Table & Drop Rate Tuning
    - **Agent:** @DataSteward, @GameBalancer
- [ ] **Issue #2:** [Feature] Auto-Adventure: Fatigue System
    - **Agent:** @GameBalancer
- [x] **Issue #3:** [Feature] Auto-Adventure: Travel Supplies (Rations & Torches)
    - **Agent:** @Equipper
- [ ] **Issue #4:** [Test] Auto-Adventure: Stress Test Scheduler
    - **Agent:** @BugHunter
- [x] **Issue #5:** [Test] Auto-Adventure: Exploit Verification
    - **Agent:** @BugHunter
    - **Status:** **Completed** (Regression Hunter added test to suite)
- [ ] **Issue #6:** [Feature] The Eldoria Codex System
    - **Agent:** @CodexKeeper
- [ ] **Issue #7:** [Feature] Alchemist Class Implementation
    - **Agent:** @Namewright, @GameForge
- [ ] **Issue #8:** [UX] Implement One UI Policy
    - **Agent:** @Palette

---

## 🛠️ Phase 5: Tech Debt & Maintenance (New)
**Focus:** Resolving critical issues identified by Issue Crafter.
- [x] **Task 5.1:** Fix Critical `pip` Vulnerability (CVE-2026-1703).
    - **Agent:** @Sentinel
    - **Status:** **Completed** (skipTest logic removed)
- [ ] **Task 5.2:** Refactor High-Complexity Methods.
    - **Agent:** @SystemSmith
    - **Subtask 5.2a:** `CombatEngine.run_combat_turn` **[x] Completed**
    - **Subtask 5.2b:** `AdventureEvents.regeneration`
    - **Subtask 5.2c:** `AdventureSession.simulate_step`
    - **Due:** 2026-03-10
- [x] **Task 5.3:** Update Grey Ward Faction (Issue #17).
    - **Agent:** @GameForge
    - **Details:** Update `factions.py` to match Namewright's design.
    - **Status:** **Completed**
- [ ] **Task 5.4:** Add Alchemist Materials (Issue #18).
    - **Agent:** @DataSteward
    - **Details:** Add `primordial_ooze`, `brimstone`, `lunawort` to `materials.py`.
    - **Due:** 2026-03-08
- [x] **Task 5.5:** Fix `"buff_data"` typo in `skills_data.py`.
    - **Agent:** @GameForge
    - **Details:** Bulk rename `"buff_data"` to `"buff"` for Alchemist, Warrior, and Rogue Class Skills.
    - **Status:** **Completed**
    - **Due:** 2026-03-08
- [x] **Task 5.6:** Add missing `"wailing_chasm"` to `adventure_locations.json`.
    - **Agent:** @GameForge
    - **Status:** **Completed**
    - **Due:** 2026-03-08
- [x] **Task 5.7:** Add missing "Choirmaster", "Blind Choir Zealot" monsters to `monsters.json`.
    - **Agent:** @GameForge
    - **Status:** **Completed**
    - **Due:** 2026-03-08
- [x] **Task 5.8:** Investigate medium-severity B310 finding in `scripts/chronicler/post_update.py:100`.
    - **Agent:** @Sentinel
    - **Status:** **Completed**
    - **Due:** 2026-03-10
- [ ] **Task 5.9:** Address ONE UI Policy violations in cogs and UI components.
    - **Agent:** @Palette
    - **Details:** `event_cog.py`, `tournament_cog.py`, `faction_cog.py`, `general_cog.py`, `developer_cog.py`, `adventure_menu.py`, `setup_view.py`, `components.py`, `handbook_view.py`.
    - **Due:** 2026-03-10
- [x] **Task 5.10:** Refactor high cyclomatic complexity functions & clean dead code.
    - **Agent:** @SystemSmith
    - **Details:** `combat_engine.py`, `consumable_manager.py`, `adventure_session.py`, `equipment_manager.py`.
    - **Status:** **Completed**
- [x] **Task 5.11:** Improve test coverage for Discord cogs.
    - **Agent:** @BugHunter
    - **Due:** 2026-03-10
- [x] **Task 5.12:** Upgrade `pip` in test environment to fix Critical CVE.
    - **Agent:** @Sentinel
    - **Status:** **Completed**
    - **Due:** 2026-03-10
- [ ] **Task 5.13:** Address ONE UI policy violations in UI components from audit report.
    - **Agent:** @Palette
    - **Due:** 2026-03-16
- [ ] **Task 5.14:** Refactor complex functions into smaller helper methods from audit report.
    - **Agent:** @SystemSmith
    - **Due:** 2026-03-16
- [ ] **Task 5.15:** Reorganize imports in test files to comply with PEP 8 from audit report.
    - **Agent:** @BugHunter
    - **Due:** 2026-03-16

---

## 🏗️ Parallel Projects

### The Alchemist Class (New)
**Design:** `.Jules/architect_designs/class_alchemist.md`
**Status:** **Implementation Phase**
- [ ] **Task A.1:** Create Alchemist Skills (Vitriol Bomb, Triage, etc.).
    - **Agent:** @GameForge / @Tactician
    - **Due:** 2026-03-08
- [x] **Task A.2:** Create Alchemist Equipment & Items.
    - **Agent:** @Equipper
    - **Status:** **Completed** (Items already exist)
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

### The Guild Halls Expansion (New)
**Design:** `.Jules/architect_designs/expansion_guild_halls.md`
**Status:** **Design Approved / Foundation Phase**
- [x] **Task GH.1:** Create `player_halls` collection and schema.
    - **Agent:** @DataSteward / @SystemSmith
    - **Status:** **Completed**
- [ ] **Task GH.2:** Tune exponential material costs for room upgrades.
    - **Agent:** @GameBalancer
    - **Due:** 2026-03-12
- [x] **Task GH.3:** Implement "Building Materials" and Boss Trophies.
    - **Agent:** @Artisan
    - **Status:** **Completed**
- [ ] **Task GH.4:** Design interactive Guild Hall management View (One UI).
    - **Agent:** @Palette
    - **Due:** 2026-03-12

### The Silent City of Ouros (New)
**Design:** `.Jules/region_silent_city_ouros.md`
**Status:** **Design Approved / Implementation Phase**
- [ ] **Task SC.1:** Connect Ouros beneath the Void Sanctum.
    - **Agent:** @DepthsWarden
    - **Due:** 2026-03-14
- [ ] **Task SC.2:** Create Temporal Wraiths, Hollowed Sentinels, Abyssal Creepers, and Chronal Dust. (Critical per Analyst report).
    - **Agent:** @GameForge
    - **Due:** 2026-03-14
- [ ] **Task SC.3:** Design the absolute silence mechanic.
    - **Agent:** @Tactician
    - **Due:** 2026-03-14
- [x] **Task SC.4:** Write oppressive flavor text for the dead city.
    - **Agent:** @StoryWeaver
    - **Due:** 2026-03-14
    - **Status:** **Completed**


---

### The Sunken Grotto (New)
**Design:** `.Jules/region_the_sunken_grotto.md`
**Status:** **Design Approved / Implementation Phase**
- [x] **Task SG.1:** Add "The Sunken Grotto" to adventure locations with Oxygen Management & Current mechanics.
    - **Agent:** @GameForge / @Grimwarden
    - **Status:** **Completed**
- [ ] **Task SG.2:** Implement aquatic monsters and resource drops.
    - **Agent:** @GameForge
    - **Due:** 2026-03-16
- [ ] **Task SG.3:** Write flavor text for The Sunken Grotto.
    - **Agent:** @StoryWeaver
    - **Due:** 2026-03-16
- [x] **Task SG.4:** Add Abyssal Rebreather equipment.
    - **Status:** **Completed**
    - **Agent:** @Equipper
    - **Due:** 2026-03-16
- [ ] **Task SG.5:** Balance oxygen drain and economy.
    - **Agent:** @GameBalancer
    - **Due:** 2026-03-16
- [ ] **Task SG.6:** Provide names for new entities.
    - **Agent:** @Namewright
    - **Due:** 2026-03-16
- [ ] **Task SG.7:** Design aquatic combat mechanics.
    - **Agent:** @Tactician
    - **Due:** 2026-03-16
- [ ] **Task SG.8:** Add achievements for region.
    - **Agent:** @ChronicleKeeper
    - **Due:** 2026-03-16
### Auto-Adventure Overhaul - Skill Tree Integrations (New)
**Design:** `.Jules/architect_designs/expansion_auto_adventure_overhaul.md`
**Status:** **Design Approved / Implementation Phase**
- [x] **Task AA.1:** Implement translation of new mechanics into `AutoCombatFormula.resolve_clash`.
    - **Agent:** @Tactician
    - **Status:** **Completed**
- [ ] **Task AA.2:** Add new paths to classes and specific skills.
    - **Agent:** @GameForge
    - **Due:** 2026-03-16

### The Lost Tomes - Skill Books (New)
**Design:** `.Jules/architect_designs/expansion_skill_books.md`
**Status:** **Design Approved / Implementation Phase**
- [ ] **Task LT.1:** Add Skill Books to `consumables.json` and `skills.json` and drop tables.
    - **Agent:** @GameForge
    - **Due:** 2026-03-15
- [ ] **Task LT.2:** Implement mechanic requirements in engine.
    - **Agent:** @Tactician
    - **Due:** 2026-03-15
- [ ] **Task LT.3:** Ensure economy balance.
    - **Agent:** @GameBalancer
    - **Due:** 2026-03-16
- [ ] **Task LT.4:** Add Forbidden Knowledge achievements.
    - **Agent:** @ChronicleKeeper
    - **Due:** 2026-03-16

### The Broken Anvil Questline (New)
**Design:** `.Jules/quest_the_broken_anvil.md`
**Status:** **Design Approved / Implementation Phase**
- [ ] **Task BA.1:** Implement `Raw Star Metal Block` and `Vial of Drake Blood` drops.
    - **Agent:** @GameForge
    - **Due:** 2026-03-16
- [x] **Task BA.2:** Review and implement dialogue.
    - **Agent:** @StoryWeaver
    - **Status:** **Completed**
- [x] **Task BA.3:** Ensure Storm Drakes and Frost Gargoyles are present in Howling Peaks.
    - **Agent:** @Grimwarden
    - **Status:** **Completed**
- [ ] **Task BA.4:** Add achievement for questline.
    - **Agent:** @ChronicleKeeper
    - **Due:** 2026-03-16

### Economy & Data Integrity Fixes (New)
**Focus:** Address severe progression gaps and schema errors found by Analyst on 2026-03-12.
- [ ] **Task E.1:** Add missing monsters (`fungal_hulk`, `spore_stalker`, `bioluminescent_myriapod`) for The Undergrove.
    - **Agent:** @GameForge / @GameBalancer
    - **Due:** 2026-03-16
- [x] **Task E.2:** Add missing materials (`fungal_spores`, `bioluminescent_sap`) for The Undergrove.
    - **Agent:** @DataSteward / @GameBalancer
    - **Due:** 2026-03-16
    - **Status:** **Completed**
- [x] **Task E.3:** Buff The Sunken Grotto economy drops to match Rank C expectations.
    - **Agent:** @GameBalancer
    - **Status:** **Completed**
- [ ] **Task E.4:** Add missing description for `howling_peaks` in `adventure_locations.json` and implement missing skills `ice_spear`/`dragon_breath`.
    - **Agent:** @GameForge / @DataSteward
    - **Due:** 2026-03-16
- [ ] **Task E.5:** Investigate and fix `whirlwind` skill missing for `storm_drake`.
    - **Agent:** @GameForge / @DataSteward
    - **Due:** 2026-03-16

### The Necromancer Class (New)
**Design:** `.Jules/architect_designs/class_necromancer.md`
**Status:** **Design Approved / Implementation Phase**
- [x] **Task N.1:** Refine lore.
    - **Agent:** @StoryWeaver
    - **Status:** **Completed**
- [ ] **Task N.2:** Evaluate `kill_heal_percent` on Life Drain.
    - **Agent:** @GameBalancer
    - **Due:** 2026-03-16
- [ ] **Task N.3:** Implement Class ID, "scythe" weapon type, and "Grave Dust".
    - **Agent:** @GameForge
    - **Due:** 2026-03-16
- [ ] **Task N.4:** Update `CombatEngine` for allied summons and `dead_enemies_count`.
    - **Agent:** @Tactician
    - **Due:** 2026-03-16

### The Crimson Citadel (New)
**Design:** `.Jules/region_the_crimson_citadel.md`
**Status:** **Design Approved / Implementation Phase**
- [ ] **Task CC.1:** Implement monsters (`crimson_templar`, `veil_behemoth`, `blood_madrigal`) and materials (`coagulated_aether`, `crimson_core`).
    - **Agent:** @GameForge
    - **Due:** 2026-03-17
- [ ] **Task CC.2:** Implement "Veil Bleed" combat/exploration hazard.
    - **Agent:** @Tactician
    - **Due:** 2026-03-17
- [ ] **Task CC.3:** Create `ward_of_astraeon` item.
    - **Agent:** @Equipper
    - **Due:** 2026-03-17
- [x] **Task CC.4:** Write flavor text and "Echoes".
    - **Agent:** @StoryWeaver
    - **Status:** **Completed**
- [ ] **Task CC.5:** Add achievements for region.
    - **Agent:** @ChronicleKeeper
    - **Due:** 2026-03-17

## 📝 Activity Log
- **2026-03-16 (Update):** Marked Tasks SC.4, N.1, and CC.4 as completed based on StoryWeaver's log. Documented Repo Auditor tasks (5.13-5.15) under Phase 5.
- **2026-03-15 (Update):** Reviewed Analyst's economy gap report (`2026-03-12_economy_and_integrity_gaps.md`) and added Subtask E.5 for missing skill `whirlwind` for `storm_drake`.
- **2026-03-14 (Update):** Integrated Analyst recommendations for The Undergrove and The Sunken Grotto. Added The Necromancer Class and The Crimson Citadel parallel projects based on Architect and Realmwright designs. Marked Tasks GH.1, SG.1, AA.1, BA.2, BA.3, and E.3 as Complete.
- **2026-03-12 (Update):** Integrated Analyst recommendations for Silent City missing monsters. Added Sunken Grotto, Auto-Adventure Skill Integrations, Lost Tomes, and Broken Anvil questline projects based on recent agent designs. Marked Issue #5, Task 5.10, and Task GH.3 as Complete.
- **2026-03-04 (Update):** Added new tasks from Repo Auditor (5.12). Marked Task 5.8 as Complete.
- **2026-03-09 (Update):** Integrated Analyst recommendations for The Silent City of Ouros drops (Task 2.2f). Noted Tech Debt Tasks 5.5, 5.6, 5.7 are Complete.
- **2026-03-02 (Update):** Added "Guild Halls" and "Silent City" parallel projects. Marked Tasks 5.1, A.2, and 2.4 completed based on 03-01/03-02 logs. Added Repo Auditor tasks (5.8-5.11). Updated 2.2 subtasks based on EV report.
- **2026-02-27:** Verified Task 3.3 (Supplies) as Complete. Added Rogue Skill Tree project and Analyst Integration tasks (2.2c/d, 2.4). Flagged Task 5.1 as CRITICAL.
- **2026-02-25 (Update):** Integrated Analyst findings (Task 2.2 split), Namewright updates (Task 3.3/Alchemist), and Issue Crafter reports (Phase 5). Marked Tasks 2.1 and 3.2 as Complete.
- **2026-02-26:** Confirmed Phase 1 (UI) and key Phase 2/3 tasks (Locations, Death Penalty, Flavor Text) are Complete. Updated plan to reflect rapid progress. Assigned remaining Fatigue and Supply tasks.
- **2026-02-25:** Phase 0 (Backend) marked Complete. Phase 1 detailed tasks assigned to @Palette and @SystemSmith.
- **2026-02-24:** Updated plan. Marked Task 0.1 and 2.1 as Complete. Re-assigned blocking Tasks 0.2 and 0.3 to SystemSmith.
- **2026-02-23:** Resumed project. Verified Phase 0.1 completion. Assigned Scheduler (0.2) and Engine (0.3) to SystemSmith.
- **2025-10-29:** Plan created. Phase 0 initiated.
