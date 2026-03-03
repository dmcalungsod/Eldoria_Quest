## 2025-02-09 — [Achievement System]

**Learning:** Testing achievement logic integrated with rewards requires mocking `DatabaseManager` carefully to avoid global `sys.modules` pollution from other tests.
**Action:** Isolate test files for new systems or use `setUp`/`tearDown` to reset `sys.modules` if modifying global mocks.

**Learning:** `active_title` defaults to `None`, which simplifies "No Title" logic in UI but requires null checks in display logic.
**Action:** Always use safe access or defaults when displaying titles.

## 2025-05-23 — [Skill Mastery Titles]

**Learning:** Integrating achievement checks into async UI callbacks (like skill learning) requires `asyncio.to_thread` to prevent blocking the event loop with synchronous DB calls.
**Action:** Always wrap `AchievementSystem` checks in `asyncio.to_thread` when calling from async contexts.

## 2026-03-08 — Shadow's Edge Rogue Achievements

**Learning:** When evaluating combat feats like "taking 0 damage," the `battle_report` dictionary tracks `damage_taken` properly. It's safer to fetch the player class dynamically via `DatabaseManager.get_player(discord_id)` inside the reward processor than to try extracting it from nested or transient objects. Using a standalone method like `check_combat_achievements` inside `AchievementSystem` keeps `AdventureRewards` clean and focused on dispatching checks.
**Action:** When implementing new class-specific combat feats, intercept the logic inside `AdventureRewards.process_victory()`, fetch current class data, and delegate the title logic cleanly to the `AchievementSystem`.
