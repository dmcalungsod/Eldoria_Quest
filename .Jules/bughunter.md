## 2026-02-27 — Fix Adventure Retreat Exploit

**Learning:** Players were able to exploit the "Retreat Early" button to escape active combat without penalty, keeping all loot. This broke the risk/reward loop of the Auto-Adventure system.
**Action:** Implemented a check in `AdventureManager.end_adventure` to detect if `active_monster` is present. If so, a 25% penalty is applied to gathered materials (Emergency Extraction). This logic is now enforced on the backend regardless of UI.
## 2026-02-28 — QA and Unit Test Fixes

**Learning:** Database `update_one` queries with strict matching criteria (e.g. `{"active": 1}`) can silently fail to update if earlier methods unexpectedly alter the target document's state before the query execution. This was occurring in `AdventureResolutionEngine` when attempting to mark a session as `"failed"` after `AdventureManager` already marked it inactive. Additionally, test suites intended to be run under a standard `unittest` framework shouldn't rely on `pytest` dependencies or fixtures unless explicitly configured in project requirements, as this causes `ModuleNotFoundError` during standard discovery.
**Action:** Always ensure the order of operations respects database document state transitions. Ensure test assertions use standard library constructs (`unittest.TestCase`) in `tests/` directories to prevent silent discovery failures by the standard test runner (`python tests/run_all_tests.py`).

## 2026-03-01 — Verify Codex unlock triggers

**Learning:** When developing the Codex System, it's crucial to correctly handle edge cases where multiple database updates might occur simultaneously or where existing documents may not have a complete schema structure. By implementing explicit fallback defaults inside the `DatabaseManager.get_codex` method, we ensure that new top-level schema additions (like `"atlas"` or `"armory"`) are automatically retrofitted onto legacy player documents during the fetch operation, preventing unexpected `KeyError` crashes in UI or logic layers. Furthermore, using precise path updates (e.g. `$set: {"bestiary.106": ...}`) prevents data overwrites when tracking discrete unlock triggers like monster kills and location visits.
**Action:** Added `tests/test_codex_unlocks.py` to assert that Codex unlocks via `update_codex` and fetches via `get_codex` behave cleanly, preserving sub-document schemas and defaulting missing top-level components during object merges. Added this file to `run_all_tests.py` so standard regression suites catch any deviation.

## 2026-03-02 — Test failure regarding `tournament_type`

**Learning:** Mock calls need to be tested for the actual expected keyword arguments. `test_start_weekly_tournament_creates_new` tested against `type` whereas `DatabaseManager.create_tournament` takes `tournament_type`.
**Action:** When updating database manager keyword arguments, always check `test_tournament_system.py` or other tests using mocked args to prevent test failures.

## 2026-03-04 — Fix Auto-Retreat Death Loop

**Learning:** Low-level players with 0 Aurum were getting soft-locked in an infinite auto-retreat death loop because their HP was preserved after death (at 1 HP, below the 15% auto-flee threshold) to prevent "free healing" exploits, but they couldn't afford the Infirmary. When they started a new expedition, the system immediately auto-retreated them without granting EXP or loot, and incorrectly penalized them for an "Emergency Extraction."

**Action:**
1. Provided free Infirmary healing for players Level 3 or below by updating `DatabaseManager.calculate_heal_cost`.
2. Added an HP check in `AdventureSetupView.start_callback` to prevent players from starting expeditions if their health is critically low (< 15%), forcing them to heal.
3. Fixed `AdventureManager.end_adventure` to only penalize for "Emergency Extraction" if the player manually clicked "Retreat Early" while in combat during an active (`in_progress`) adventure, ignoring auto-retreats natively completed by the background engine.

## 2026-03-04 — Fix Mock assertions in tests/test_codex_unlocks.py

**Learning:** When using nested `__getitem__` calls in `DatabaseManager._col`, assertions on mock objects must mimic the exact chain of `__getitem__` calls made by the code under test (e.g., `self.mock_client().__getitem__('EQ_Game').__getitem__('player_codex')`) to ensure the correct mocked collection is targeted for assertions.
**Action:** Updated test assertions in `tests/test_codex_unlocks.py` to fetch the correctly nested mock object before asserting `update_one` calls, fixing the pipeline.
## 2026-03-11 — Fix Codex Unlocks Test Mock Assertions

**Learning:** When using nested `__getitem__` calls in `DatabaseManager._col`, assertions on mock objects must mimic the exact chain of `__getitem__` calls made by the code under test (e.g., `self.mock_client.__getitem__(self.db._db_name).__getitem__('player_codex')`) to ensure the correct mocked collection is targeted for assertions. `self.mock_db` alone is not enough, as `DatabaseManager` accesses the database name first via the client before the collection name.
**Action:** Updated test assertions in `tests/test_codex_unlocks.py` to fetch the correctly nested mock object before asserting `update_one` calls, fixing the pipeline and resolving Codex Tests failures.
## 2026-03-12 — Added Guild Advisor Checklist Tests

**Learning:** When writing tests that use discord modules it's essential to not just stub the module `discord` but also specific properties and classes used (e.g., `discord.Embed`, `discord.Color`) properly with robust mocking implementations (e.g., mock classes). Also, when changing test imports inside test suites like `tests/run_all_tests.py`, verify not just that individual tests run properly but also that the `run_all_tests.py` comprehensive test suite passes fully to prevent regression `ImportError` bugs.

**Action:** Before running tests always double check what dependencies need to be specifically patched and ensure `PYTHONPATH=. python tests/run_all_tests.py` finishes flawlessly after any refactoring.
## 2026-03-14 — Fix Codex Test Assertions Mock Mapping

**Learning:** When using mock setups in tests (e.g. `test_codex_unlocks.py`), asserting on deeply chained `__getitem__` mock objects like `self.mock_client.__getitem__(self.db._db_name).__getitem__("player_codex")` can fail because the test runner interprets the reference differently than the system under test (`DatabaseManager`), leading to assertion mismatches (`Expected call not found`).
**Action:** Always retrieve the mock object for assertion using the same internal method the system uses. In this case, `self.db._col("player_codex")` correctly returns the patched Mock object that the `update_one` and `find_one` calls were actually made against.
