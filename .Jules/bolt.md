## 2024-05-23 — Mixed Updates in MongoDB

**Learning:** MongoDB allows mixing `$set` and `$inc` operators in a single `update_one` call, provided they target different fields.
**Action:** Use `update_player_mixed` pattern when updating absolute values (like HP) and relative values (like Vestige) simultaneously to save a round-trip.

## 2024-10-25 — Caching Mutable Objects

**Learning:** When caching mutable objects (like dictionaries) in a singleton manager, always return a `copy()` to the caller. Returning a reference allows callers to accidentally mutate the shared cache, leading to subtle state corruption across the application.
**Action:** Use `.copy()` (or deepcopy if necessary) when returning cached objects from `DatabaseManager`.
