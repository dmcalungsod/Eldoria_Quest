# 🐞 NEW ISSUES

## 1. [Feature] Auto-Adventure: Loot Table & Drop Rate Tuning
**Description:**
- **Source:** Foreman Plan (Phase 2, Task 2.2)
- **Details:** Configure loot tables and drop rates for Auto-Adventures to ensure economy balance (materials vs time). Pending comprehensive review.
- **Acceptance Criteria:**
  - Define drop rates for all adventure locations.
  - Verify material income matches expected hourly rates.
  - Update `game_systems/data/loot_tables.py` (or equivalent).
- **Labels:** `enhancement`, `balance`, `economy`
- **Assignee:** @DataSteward, @GameBalancer

## 2. [Feature] Auto-Adventure: Fatigue System
**Description:**
- **Source:** Foreman Plan (Phase 2, Task 2.3)
- **Details:** Modify `AdventureResolutionEngine` to increase monster damage scaling for long durations to simulate fatigue. Specifically, increase monster ATK by 5% per hour after the 4th hour.
- **Acceptance Criteria:**
  - Implement fatigue logic in `AdventureResolutionEngine`.
  - Add unit tests verifying damage scaling over time.
  - Update `AdventureSession` to track fatigue state if necessary.
- **Labels:** `enhancement`, `mechanic`
- **Assignee:** @GameBalancer

## 3. [Feature] Auto-Adventure: Travel Supplies (Rations & Torches)
**Description:**
- **Source:** Foreman Plan (Phase 3, Task 3.3)
- **Details:** Implement items and UI selector for travel supplies.
  - `Rations`: Provide auto-heal functionality.
  - `Torches`: Reduce ambush chance or enable night exploration.
- **Acceptance Criteria:**
  - Create item data for Rations and Torches.
  - Add UI selector in `AdventureSetupView`.
  - Implement usage logic in `AdventureSession`.
- **Labels:** `enhancement`, `items`, `ui`
- **Assignee:** @Equipper

## 4. [Test] Auto-Adventure: Stress Test Scheduler
**Description:**
- **Source:** Foreman Plan (Phase 4, Task 4.1)
- **Details:** Stress test the background scheduler (`cogs/adventure_loop.py`) with 10,000 simulated sessions to ensure performance and stability.
- **Acceptance Criteria:**
  - Create a test script to generate 10k mock sessions.
  - Measure scheduler loop time and database load.
  - Verify no dropped updates or race conditions.
- **Labels:** `testing`, `performance`
- **Assignee:** @BugHunter

## 5. [Test] Auto-Adventure: Exploit Verification
**Description:**
- **Source:** Foreman Plan (Phase 4, Task 4.2)
- **Details:** Verify prevention of the "Cancel" exploit where players might cancel an adventure just before failure to avoid penalties.
- **Acceptance Criteria:**
  - Attempt to cancel adventure during combat resolution phase.
  - Verify that state is locked or penalties apply correctly.
  - Document findings and fix if exploit exists.
- **Labels:** `testing`, `security`
- **Assignee:** @BugHunter

## 6. [Feature] The Eldoria Codex System
**Description:**
- **Source:** Architect Design (`codex_system.md`) / Feedback
- **Details:** Implement a living encyclopedia (Bestiary, Atlas, Armory) that fills as players explore.
- **Acceptance Criteria:**
  - Implement `CodexCog` and `/codex` command.
  - Create `player_codex` schema in `DatabaseManager`.
  - Add hooks in `CombatEngine` and `AdventureSession` to track kills/visits.
  - Create UI Embeds for Bestiary, Atlas, and Armory.
- **Labels:** `feature`, `content`, `ui`
- **Assignee:** @CodexKeeper

## 7. [Feature] Alchemist Class Implementation
**Description:**
- **Source:** Visionary Strategy / Feedback
- **Details:** Design and implement the Alchemist class, focusing on healing and survival utility ("Suture & Salve", "Vitriol Phial").
- **Acceptance Criteria:**
  - Finalize skill names and mechanics.
  - Implement class in `skills_data.py`.
  - Add class-specific items (e.g., Alchemist's Kit).
- **Labels:** `feature`, `class`, `content`
- **Assignee:** @Namewright (Design), @GameForge (Implementation)

## 8. [UX] Implement One UI Policy
**Description:**
- **Source:** Feedback / General UX
- **Details:** Review existing interfaces and consolidate them to reduce clutter, following the "One UI" policy (edit messages instead of sending new ones where possible).
- **Acceptance Criteria:**
  - Audit `tournament_cog.py`, `event_cog.py`, `onboarding_cog.py`.
  - Refactor to use persistent views and message editing.
  - Ensure consistent visual style.
- **Labels:** `enhancement`, `ui`, `ux`
- **Assignee:** @Palette

## 9. [Feature] Warrior Skill Tree Expansion
**Description:**
- **Source:** Architect Design (2026-02-27)
- **Details:** Transform the Warrior class with two distinct playstyles: Juggernaut (Tank) and Berserker (DPS). Introduce 7 new skills and new combat mechanics.
- **Acceptance Criteria:**
  - Implement 7 new skills in `skills_data.py` including Shield Bash, Reckless Swing, Iron Skin, Bloodlust, Taunt, Whirlwind, and Unstoppable Force.
  - Update `CombatEngine` to support new mechanics: `self_damage_percent` (recoil), `kill_heal_percent` (heal on kill), and `status_immunity`.
  - Add titles/achievements for mastering paths ("Ironclad", "Ravager", "Unstoppable").
- **Labels:** `feature`, `class`, `mechanic`
- **Assignee:** @GameForge, @Tactician, @ChronicleKeeper

## 10. [Security] Critical pip Vulnerability (CVE-2026-1703)
**Description:**
- **Source:** Repo Auditor (2026-03-01)
- **Details:** A critical vulnerability exists in `pip` version 25.3 (CVE-2026-1703), allowing potential arbitrary code execution.
- **Acceptance Criteria:**
  - Upgrade `pip` to version 26.0 or later immediately.
  - Verify environment stability after upgrade.
- **Labels:** `security`, `dependency`, `priority-critical`
- **Assignee:** @Sentinel

## 11. [Tech Debt] Refactor CombatEngine.run_combat_turn
**Description:**
- **Source:** Repo Auditor (2026-03-01)
- **Details:** Cyclomatic Complexity Score of F (43) detected in `CombatEngine.run_combat_turn`. The method is too complex and prone to bugs.
- **Acceptance Criteria:**
  - Refactor `run_combat_turn` into smaller helper methods (e.g., `_resolve_status_effects`, `_calculate_damage`, `_process_turn_phases`).
  - Ensure logic remains functionally identical.
  - Reduce complexity score below 15.
- **Labels:** `refactoring`, `tech-debt`, `priority-high`
- **Assignee:** @SystemSmith

## 12. [Tech Debt] Refactor AdventureEvents.regeneration
**Description:**
- **Source:** Repo Auditor (2026-03-01)
- **Details:** Cyclomatic Complexity Score of E (35) detected in `AdventureEvents.regeneration`. Logic for flavor text and calculations is intertwined.
- **Acceptance Criteria:**
  - Split logic into `_calculate_regen` (mechanics) and `_get_regen_flavor` (text).
  - Reduce complexity score below 15.
- **Labels:** `refactoring`, `tech-debt`
- **Assignee:** @SystemSmith

## 13. [Tech Debt] Refactor AdventureSession.simulate_step
**Description:**
- **Source:** Repo Auditor (2026-03-01)
- **Details:** Cyclomatic Complexity Score of E detected in `AdventureSession.simulate_step`. The core adventure loop is becoming a monolithic method.
- **Acceptance Criteria:**
  - Decompose step simulation into distinct phases (e.g., `_handle_event`, `_handle_combat`, `_handle_loot`).
  - Ensure maintainability of the core loop.
- **Labels:** `refactoring`, `tech-debt`
- **Assignee:** @SystemSmith
