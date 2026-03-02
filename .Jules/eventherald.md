## 2026-03-03 — Location-Specific Event Modifiers

**Learning:** Implementing location-specific event modifiers (like increased loot only in Frostfall) requires passing `location_id` through `AdventureSession.simulate_step` down to `AdventureRewards.process_victory` and `_process_loot_and_quests`, as `AdventureRewards` is initialized without location context.
**Action:** Ensure future event implementations that rely on location context update the reward processing pipeline to include `location_id`.
## 2026-03-01 — Centralizing Location Bonuses

**Learning:** When adding event bonuses tied to specific newly created regions, tests must mock out external location data schemas and mock the external random and math behaviors appropriately to avoid failing tests during standard event verification. In `tests/run_all_tests.py`, new event test modules must be manually imported and added to the suite so that they run properly in CI loops.
**Action:** Always import and register newly created test files inside the master `tests/run_all_tests.py` script.

## 2026-03-02 — The Silent City of Ouros 'Time Quake' Event

**Learning:** When adding location-specific events (e.g., threat reduction or loot bonus for a single zone like Ouros), placing logical checks inside `simulate_step` and `_process_loot_and_quests` effectively ensures those regions offer temporary mechanical incentives that can be safely overridden globally. Testing these hooks thoroughly requires mocking out variables inside `AdventureSession` directly to check passing context variables.
**Action:** Moving forward, similar location-specific buffs can be structured this way, but they should eventually be migrated into a centralized status effect processor rather than polluting `adventure_session.py` with individual `if location_id == X:` checks.
