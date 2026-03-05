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
## 2026-03-03 — Auto-Adventure Overhaul Scheduler Regression Test

**Learning:** When testing background tasks like `discord.ext.tasks.loop`, it's crucial to mock the loop decorator properly to avoid `StopIteration` errors when interacting with test frameworks like `unittest.mock`. Also, `cogs` require complete module mocks for `discord`, `discord.ext`, and `discord.ext.commands` before they can be safely imported without Discord API dependencies in isolated unit tests.
**Action:** Implemented `tests/test_adventure_loop_regression.py` to cover the `AdventureLoop` scheduler cog. The test verifies that `get_adventures_ending_before` correctly fetches expired sessions based on the current `WorldTime` and successfully passes them to `AdventureResolutionEngine.resolve_sessions_batch` while handling empty states and catching exceptions to prevent crashes. Integrated the new test into `tests/run_all_tests.py`.

## 2026-03-05 - Scheduler Stress Test & Mock Isolation
- **Learnings:**
  - **Test Pollution:** When multiple UI test files globally mock `discord` objects (like `discord.Embed`) in varying ways (e.g., as `MagicMock` vs custom struct classes), standard discovery tools like `pytest` run them sequentially in the same process, causing massive test pollution and false-negative failures. Solved by injecting fallback inspection mechanisms into the test assertions directly (`hasattr(embed.add_field, 'call_args_list')`) rather than relying on assumed mock object structures.
  - **Module Mocks:** Always isolate module mocks using `patch.dict(sys.modules)` within `setUp` or test methods rather than at the root file level to prevent cross-contamination.
  - **Performance Assertions:** Translated a manual stress testing script (`stress_adventure_realistic.py`) into an automated `unittest.TestCase` regression test. This guarantees that engine refactors won't silently degrade the throughput required for the Auto-Adventure background loop (10,000 sessions/minute).
