## 2025-02-09 — [Achievement System]

**Learning:** Testing achievement logic integrated with rewards requires mocking `DatabaseManager` carefully to avoid global `sys.modules` pollution from other tests.
**Action:** Isolate test files for new systems or use `setUp`/`tearDown` to reset `sys.modules` if modifying global mocks.

**Learning:** `active_title` defaults to `None`, which simplifies "No Title" logic in UI but requires null checks in display logic.
**Action:** Always use safe access or defaults when displaying titles.

## 2025-05-23 — [Skill Mastery Titles]

**Learning:** Integrating achievement checks into async UI callbacks (like skill learning) requires `asyncio.to_thread` to prevent blocking the event loop with synchronous DB calls.
**Action:** Always wrap `AchievementSystem` checks in `asyncio.to_thread` when calling from async contexts.
