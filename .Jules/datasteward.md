## 2025-05-27 — Adventure Locations Data Migration

**Learning:** `adventure_locations.py` contained hardcoded dictionary data that included tuples (e.g., `("monster_id", weight)`). JSON does not support tuples, converting them to lists. Existing game logic relies on these being tuples (or at least iterable pairs).
**Action:** When migrating data to JSON, ensure the loader script explicitly converts specific list fields back to tuples if strict backward compatibility is required, or verify that the codebase treats lists and tuples interchangeably. Implemented automatic tuple reconstruction in `adventure_locations.py` for `monsters`, `night_monsters`, and `gatherables`.
