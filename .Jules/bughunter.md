## 2026-02-27 — Fix Adventure Retreat Exploit

**Learning:** Players were able to exploit the "Retreat Early" button to escape active combat without penalty, keeping all loot. This broke the risk/reward loop of the Auto-Adventure system.
**Action:** Implemented a check in `AdventureManager.end_adventure` to detect if `active_monster` is present. If so, a 25% penalty is applied to gathered materials (Emergency Extraction). This logic is now enforced on the backend regardless of UI.
## 2026-02-28 — QA and Unit Test Fixes

**Learning:** Database `update_one` queries with strict matching criteria (e.g. `{"active": 1}`) can silently fail to update if earlier methods unexpectedly alter the target document's state before the query execution. This was occurring in `AdventureResolutionEngine` when attempting to mark a session as `"failed"` after `AdventureManager` already marked it inactive. Additionally, test suites intended to be run under a standard `unittest` framework shouldn't rely on `pytest` dependencies or fixtures unless explicitly configured in project requirements, as this causes `ModuleNotFoundError` during standard discovery.
**Action:** Always ensure the order of operations respects database document state transitions. Ensure test assertions use standard library constructs (`unittest.TestCase`) in `tests/` directories to prevent silent discovery failures by the standard test runner (`python tests/run_all_tests.py`).

## 2026-03-01 — Verify Codex unlock triggers

**Learning:** When developing the Codex System, it's crucial to correctly handle edge cases where multiple database updates might occur simultaneously or where existing documents may not have a complete schema structure. By implementing explicit fallback defaults inside the `DatabaseManager.get_codex` method, we ensure that new top-level schema additions (like `"atlas"` or `"armory"`) are automatically retrofitted onto legacy player documents during the fetch operation, preventing unexpected `KeyError` crashes in UI or logic layers. Furthermore, using precise path updates (e.g. `$set: {"bestiary.106": ...}`) prevents data overwrites when tracking discrete unlock triggers like monster kills and location visits.
**Action:** Added `tests/test_codex_unlocks.py` to assert that Codex unlocks via `update_codex` and fetches via `get_codex` behave cleanly, preserving sub-document schemas and defaulting missing top-level components during object merges. Added this file to `run_all_tests.py` so standard regression suites catch any deviation.
