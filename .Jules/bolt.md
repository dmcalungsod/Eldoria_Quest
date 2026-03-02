## 2024-05-23 — Redundant World Event Lookups

**Learning:** The `AdventureSession` logic was fetching world events twice per step: once to get modifiers via `get_modifiers()` and once to get the event type via `get_current_event()`. This doubled the overhead of `DatabaseManager.get_active_world_event` calls (cache checks + potential DB queries + datetime parsing + dict copying).
**Action:** Always inspect helper methods like `get_modifiers` to see if they wrap a call you are already making. Consolidate calls to fetching the main object (e.g., `get_current_event`) and extract derived data (modifiers) from it locally.

## 2024-05-23 - [Centralized Database Caching Pattern]
**Learning:** High-frequency access to slowly changing global data (like global boosts) created redundant DB queries across different modules (`AdventureSession` vs `CombatHandler`). Consumer-side caching in `CombatHandler` was incomplete (no invalidation) and missed by other consumers.
**Action:** Move caching logic to the data source (`DatabaseManager`). Use simple TTL + Write-Invalidation. This improves performance for all consumers and ensures data consistency.

## 2024-05-24 - [Adventure Loop N+1 Query]
**Learning:** `AdventureSession.simulate_step` triggered redundant DB queries by checking auto-combat conditions (fetching stats/vitals) then re-fetching them for combat execution. This doubled the query load for every single turn.
**Action:** Lift data fetching to the parent method (`simulate_step`) using a context object. Pass this context to decision logic and execution logic. Reduces queries by ~20% per step.

## 2024-05-24 - [Combat Stat Caching]
**Learning:** Repeated property access in `PlayerStats` (which calculates totals on-the-fly) during combat loops added significant overhead, especially in auto-combat.
**Action:** Pre-calculate a `stats_dict` once per adventure step and pass it to `CombatEngine`. Updated `DamageFormula` to handle dictionary inputs efficiently. Added robust fallbacks for critical stats like Max HP to prevent logic errors if the cache is malformed.

## 2024-05-25 - [Redundant Buff Cleanup on Hot Path]
**Learning:** `AdventureSession` was executing a `DELETE` query (`clear_expired_buffs`) on every single turn/step to maintain `active_buffs` table hygiene. However, the read query (`get_active_buffs`) already filters out expired rows by timestamp.
**Action:** Removed the `DELETE` operation from the hot path `_fetch_combat_context`. Moved the cleanup logic to `AdventureManager.start_adventure`, ensuring the table is pruned only when a new session begins (cold path), saving 1 write operation per turn.

## 2024-05-26 - [Pre-parsing JSON in Database Layer]
**Learning:** `CombatHandler` was parsing `buff_data` (JSON string) for every skill on every combat turn because MongoDB stores it as a string. This deserialization overhead accumulated in loops.
**Action:** Implemented caching in `DatabaseManager` (`_skill_cache`) that parses `buff_data` once on load. Exposed pre-parsed dicts to consumers, removing redundant parsing logic from the hot path.

## 2026-03-01 - [Auto-Adventure Scheduler N+1 Query Fix]
**Learning:** `AdventureResolutionEngine.resolve_sessions_batch` fetched combat context bundles inside a loop calling `get_combat_context_bundle` for each `discord_id`, resulting in an N+1 query problem that slowed down the auto-adventure scheduler.
**Action:** Introduced `get_combat_context_bundles_batch` using MongoDB's `$in` operator to fetch all context bundles in a single query. `resolve_sessions_batch` now parses and maps these bundles, passing them efficiently into `resolve_session`.

## 2026-03-02 — Optimizing the Auto-Adventure Scheduler Query

**Learning:** The auto-adventure background scheduler (`cogs/adventure_loop.py`) runs frequently (every minute) and searches for completed adventures using a specific time-based query (`get_adventures_ending_before` in `database/database_manager.py`). Without a proper composite index covering all the query's match conditions (`active`, `status`, `end_time`), MongoDB falls back to a collection scan, leading to O(N) performance degradation as the active user base grows (which is catastrophic for a scheduler intended to handle 10k+ concurrent sessions).
**Action:** Always ensure that background polling queries targeting expanding collections have covering indexes. In Eldoria Quest, these indexes must be explicitly registered within the `INDEX_DEFINITIONS` dictionary in `database/create_database.py` to be correctly initialized.
