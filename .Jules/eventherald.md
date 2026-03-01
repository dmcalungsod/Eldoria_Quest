## 2026-03-03 — Location-Specific Event Modifiers

**Learning:** Implementing location-specific event modifiers (like increased loot only in Frostfall) requires passing `location_id` through `AdventureSession.simulate_step` down to `AdventureRewards.process_victory` and `_process_loot_and_quests`, as `AdventureRewards` is initialized without location context.
**Action:** Ensure future event implementations that rely on location context update the reward processing pipeline to include `location_id`.
## 2026-03-01 — Centralizing Location Bonuses

**Learning:** When adding event bonuses tied to specific newly created regions, tests must mock out external location data schemas and mock the external random and math behaviors appropriately to avoid failing tests during standard event verification. In `tests/run_all_tests.py`, new event test modules must be manually imported and added to the suite so that they run properly in CI loops.
**Action:** Always import and register newly created test files inside the master `tests/run_all_tests.py` script.
