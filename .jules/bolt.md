## 2024-05-23 - [Centralized Database Caching Pattern]
**Learning:** High-frequency access to slowly changing global data (like global boosts) created redundant DB queries across different modules (`AdventureSession` vs `CombatHandler`). Consumer-side caching in `CombatHandler` was incomplete (no invalidation) and missed by other consumers.
**Action:** Move caching logic to the data source (`DatabaseManager`). Use simple TTL + Write-Invalidation. This improves performance for all consumers and ensures data consistency.

## 2024-05-24 - [Adventure Loop N+1 Query]
**Learning:** `AdventureSession.simulate_step` triggered redundant DB queries by checking auto-combat conditions (fetching stats/vitals) then re-fetching them for combat execution. This doubled the query load for every single turn.
**Action:** Lift data fetching to the parent method (`simulate_step`) using a context object. Pass this context to decision logic and execution logic. Reduces queries by ~20% per step.
