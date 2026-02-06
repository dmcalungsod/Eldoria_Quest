## 2024-05-23 - [Centralized Database Caching Pattern]
**Learning:** High-frequency access to slowly changing global data (like global boosts) created redundant DB queries across different modules (`AdventureSession` vs `CombatHandler`). Consumer-side caching in `CombatHandler` was incomplete (no invalidation) and missed by other consumers.
**Action:** Move caching logic to the data source (`DatabaseManager`). Use simple TTL + Write-Invalidation. This improves performance for all consumers and ensures data consistency.
