## 2026-03-03 — Location-Specific Event Modifiers

**Learning:** Implementing location-specific event modifiers (like increased loot only in Frostfall) requires passing `location_id` through `AdventureSession.simulate_step` down to `AdventureRewards.process_victory` and `_process_loot_and_quests`, as `AdventureRewards` is initialized without location context.
**Action:** Ensure future event implementations that rely on location context update the reward processing pipeline to include `location_id`.
## 2026-03-01 — Centralizing Location Bonuses

**Learning:** When adding event bonuses tied to specific newly created regions, tests must mock out external location data schemas and mock the external random and math behaviors appropriately to avoid failing tests during standard event verification. In `tests/run_all_tests.py`, new event test modules must be manually imported and added to the suite so that they run properly in CI loops.
**Action:** Always import and register newly created test files inside the master `tests/run_all_tests.py` script.

## 2026-03-02 — The Silent City of Ouros 'Time Quake' Event

**Learning:** When adding location-specific events (e.g., threat reduction or loot bonus for a single zone like Ouros), placing logical checks inside `simulate_step` and `_process_loot_and_quests` effectively ensures those regions offer temporary mechanical incentives that can be safely overridden globally. Testing these hooks thoroughly requires mocking out variables inside `AdventureSession` directly to check passing context variables.
**Action:** Moving forward, similar location-specific buffs can be structured this way, but they should eventually be migrated into a centralized status effect processor rather than polluting `adventure_session.py` with individual `if location_id == X:` checks.

## 2026-03-05 — The Fungal Bloom

**Learning:** Implementing location-specific event modifiers (like increased loot and threat reduction only in The Undergrove) requires passing specific keys through the `WorldEventSystem.EVENT_CONFIGS` into the active buffs context. Hooking into these requires explicitly grabbing them via `combat_result.get("active_boosts", {}).get("undergrove_loot_bonus", 1.0)` during loot processing, and similarly checking for `undergrove_threat_reduction` during `AdventureSession._calculate_threat_reduction`.
**Action:** Ensure future event implementations that rely on location context add those custom tags into `EVENT_CONFIGS` properly and then hook them where appropriate in the processing pipeline.

## 2026-03-05 — The Permafrost Thaw

**Learning:** Implementing location-specific events tied to new regions (like The Permafrost Thaw for Frostmire) follows the established pattern of hooking `loot_boost` and `threat_reduction` through `_process_loot_and_quests` and `simulate_step`.
**Action:** Always test newly created event modifications thoroughly by mocking context properly. Ensure new test files are wired correctly into `run_all_tests.py` using `unittest` loader methods.
## 2026-03-13 — The Abyssal Tide

**Learning:** Implementing location-specific events tied to new regions (like The Abyssal Tide for The Sunken Grotto) continues to follow the established pattern of hooking `loot_boost` and `threat_reduction` through `AdventureRewards._process_loot_and_quests` and `AdventureSession.simulate_step`.
**Action:** Always test newly created event modifications properly to ensure the location IDs align exactly with those in `adventure_locations.json` and that modifiers stack correctly with other events if any exist.
