## 2025-02-09 — [Achievement System]

**Learning:** Testing achievement logic integrated with rewards requires mocking `DatabaseManager` carefully to avoid global `sys.modules` pollution from other tests.
**Action:** Isolate test files for new systems or use `setUp`/`tearDown` to reset `sys.modules` if modifying global mocks.

**Learning:** `active_title` defaults to `None`, which simplifies "No Title" logic in UI but requires null checks in display logic.
**Action:** Always use safe access or defaults when displaying titles.
