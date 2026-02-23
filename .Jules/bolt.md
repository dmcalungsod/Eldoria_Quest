## 2024-05-23 — Redundant World Event Lookups

**Learning:** The `AdventureSession` logic was fetching world events twice per step: once to get modifiers via `get_modifiers()` and once to get the event type via `get_current_event()`. This doubled the overhead of `DatabaseManager.get_active_world_event` calls (cache checks + potential DB queries + datetime parsing + dict copying).
**Action:** Always inspect helper methods like `get_modifiers` to see if they wrap a call you are already making. Consolidate calls to fetching the main object (e.g., `get_current_event`) and extract derived data (modifiers) from it locally.
