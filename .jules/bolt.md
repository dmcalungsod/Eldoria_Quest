# Bolt's Journal - Critical Learnings

## 2024-05-22 - Centralized Caching
**Learning:** Moved ad-hoc caching from `CombatHandler` to `DatabaseManager`.
**Insight:** Caching at the source (DB layer) benefits all consumers and ensures consistency. Ad-hoc caching in consumers leads to duplicate logic and potential inconsistencies (e.g. one consumer has stale data while another has fresh).
**Action:** Always look for opportunities to move caching logic "upstream" to the data source.
