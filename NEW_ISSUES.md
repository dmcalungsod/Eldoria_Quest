# Issue Crafter: New Issues

**Title:** [Feature] Rogue Skill Tree Expansion ("Shadow's Edge")

**Description:**
- **Source:** Architect Design (`.Jules/architect_designs/skill_tree_rogue.md`) & Agent Log 2026-03-08
- **Details:** Implement the "Assassin" and "Phantom" skill paths for the Rogue class to differentiate playstyles.
- **Requirements:**
  - **Skills (GameForge):**
    - `double_strike` (Active, Tier 1): 2x hit, DEX scaling.
    - `stealth` (Passive, Tier 1): +10% AGI.
    - `toxic_blade` (Active, Tier 2): Weak hit + Poison.
    - `shadow_step` (Active, Tier 2): +Evasion, `next_hit_crit` buff.
    - `venomous_strike` (Active, Tier 3): Bonus dmg if target poisoned.
    - `flash_powder` (Active, Tier 3): AoE Blind (-Accuracy).
    - `death_blossom` (Ultimate, Rank A): AoE Damage + Bleed.
  - **Mechanics (Tactician):**
    - Implement `next_hit_crit` flag in `CombatEngine` (guarantees crit on next attack).
    - Implement `conditional_multiplier` in `DamageFormula` (check `target_poisoned`).
    - Implement `accuracy_percent` debuff logic in `MonsterAI` or `DamageFormula`.
  - **Achievements (ChronicleKeeper):**
    - Title: "Assassin" (Unlock Assassin path).
    - Title: "Phantom" (Unlock Phantom path).
    - Achievement: "Unseen Death" (Win battle w/o taking damage as Rogue).
- **Labels:** `feature`, `class-rogue`, `mechanics`
- **Assignee:** @GameForge, @Tactician

**Title:** [Balance] Economy Imbalance in Adventure Locations

**Description:**
- **Source:** Analyst log 2026-03-01 & Visionary memo 2026-03-01
- **Details:** Analyst EV modeling highlights significant economy imbalances in Phase 2 auto-adventure locations.
- **Acceptance criteria:**
  - Buff drop rates/rewards for *The Shrouded Fen* (EV ~192) and *The Clockwork Halls* (EV ~533) to match their intended levels.
  - Heavily nerf *The Molten Caldera* (EV ~1500) so it doesn't outclass Rank A zones.
- **Labels:** `balance`, `economy`, `adventure`
- **Assignee:** @GameBalancer

**Title:** [Feature] Implement The Silent City of Ouros Region Mechanics & Content

**Description:**
- **Source:** Realmwright log 2026-03-01
- **Details:** A new Rank S endgame location, "The Silent City of Ouros", has been designed and added to `adventure_locations.json`.
- **Acceptance criteria:**
  - @GameForge: Add new monsters (Temporal Wraith, Hollowed Sentinel) and gatherables with stats.
  - @Tactician: Design a silence mechanic that disables sound-based skills.
  - @DepthsWarden: Connect this region beneath the Void Sanctum in the dungeon hierarchy.
- **Labels:** `feature`, `content`, `region`
- **Assignee:** @GameForge, @Tactician, @DepthsWarden

**Title:** [Bug] Fix "buff_data" typo in skills_data.py

**Description:**
- **Source:** Visionary memo 2026-03-01 (Nexus report)
- **Steps to reproduce:** Use Alchemist skills in combat engine.
- **Expected behavior:** Buffs should apply correctly using the `"buff"` key.
- **Actual behavior:** Alchemist skills use the incorrect `"buff_data"` key instead of `"buff"`, breaking existing combat engine logic.
- **Suggested fix:** Rename `"buff_data"` to `"buff"` in `game_systems/data/skills_data.py` for all Alchemist skills.
- **Labels:** `bug`, `skills`, `priority-high`
- **Assignee:** @GameForge

**Title:** [Bug] Missing Monsters for "The Blind Choir's Requiem"

**Description:**
- **Source:** Visionary memo 2026-03-01 (Nexus report)
- **Details:** The newly added "The Blind Choir's Requiem" questline references monsters that don't exist yet, causing an implicit dependency break.
- **Steps to reproduce:** Attempt to progress "The Blind Choir's Requiem" questline.
- **Expected behavior:** Quest encounters should function normally.
- **Actual behavior:** Fails because "Choirmaster" and "Blind Choir Zealot" are missing.
- **Suggested fix:** Add "Choirmaster" and "Blind Choir Zealot" to `game_systems/data/monsters.json`.
- **Labels:** `bug`, `content`, `monsters`
- **Assignee:** @GameForge

**Title:** [Bug] Missing schema fields in Frostfall Expanse locations

**Description:**
- **Source:** Visionary memo 2026-03-01 (Nexus report)
- **Details:** Frostfall Expanse locations in `adventure_locations.json` might be missing required `floor_depth` and `danger_level` fields, as flagged by Nexus.
- **Steps to reproduce:** Validate `adventure_locations.json` against schema.
- **Expected behavior:** All locations must have required schema fields.
- **Actual behavior:** Missing `floor_depth` and `danger_level` fields.
- **Suggested fix:** Verify and fix the `adventure_locations.json` schema to ensure `floor_depth` and `danger_level` are present.
- **Labels:** `bug`, `data`, `schema`
- **Assignee:** @DataSteward

**Title:** [Tech Debt] Refactor High Cyclomatic Complexity in Core/UI methods

**Description:**
- **Source:** Repo Auditor report 2026-03-01
- **Details:** High cyclomatic complexity found in several core and UI methods, making them hard to maintain and test.
- **Acceptance criteria:**
  - Refactor `detect_element` in `game_systems/core/world_time.py` (Complexity: 30)
  - Refactor `apply_weather_modifiers` in `game_systems/adventure/adventure_events.py` (Complexity: 21)
  - Refactor `build_inventory_embed` in `cogs/utils/ui_helpers.py` (Complexity: 21)
  - Refactor `load_locations` in `game_systems/data/database_manager.py` (Complexity: 15)
  - Break down complex UI building and event processing methods into smaller, testable helpers.
- **Labels:** `tech-debt`, `refactor`
- **Assignee:** @SystemSmith

**Title:** [Tech Debt] Remove Dead Code (Unused Variables)

**Description:**
- **Source:** Repo Auditor report 2026-03-01
- **Details:** Dead code (unused variables) discovered by vulture clutters the codebase and can cause confusion.
- **Acceptance criteria:**
  - Remove unused variables in `scripts/analysis/analyze_economy.py`
  - Remove unused variables in `scripts/analysis/check_progression_gaps.py`
  - Remove unused variables in various test files (e.g. `tests/stress_adventure_realistic.py`, `tests/test_quest_branching.py`) identified by Vulture.
- **Labels:** `tech-debt`, `cleanup`
- **Assignee:** @SystemSmith, @BugHunter
