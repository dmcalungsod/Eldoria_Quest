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
