# Regression Hunter Journal

## Critical Learnings

### 2024-05-23: Adventure Death Penalty
- **Area:** Adventure System / Economy
- **Risk:** High (Economy inflation if penalties fail)
- **Test:** `tests/test_adventure_death_penalty.py`
- **Pattern:** Mocking `AdventureSession` class within `game_systems.adventure.adventure_manager` allowed control over internal session state (`loot`) and behavior (`simulate_step` returning `dead=True`), avoiding complex setup of a real session.
- **Key Insight:** `AdventureManager` calculates penalties based on *current* player Aurum (database fetch) and *session* loot. Testing both requires mocking DB returns and session object state simultaneously.

### 2026-03-01: Auto-Adventure Regression Testing & CI Integration
- **Area:** Auto-Adventure System / Combat Formula
- **Risk:** High (Core gameplay loop breakage during scaling)
- **Changes:** `tests/test_auto_adventure_regression.py`, `tests/test_adventure_resolution.py`, and `tests/test_auto_combat_formula.py` were integrated into `tests/run_all_tests.py` to ensure that standard local runs properly execute these regression and unit tests.
- **Key Insight:** To maintain stability of the Auto-Adventure mechanics, including fatigue, supply consumption, and deterministic combat formulas, these tests needed to be run locally in standard suites along with CI hooks to protect new content development in Phase 2/3.
