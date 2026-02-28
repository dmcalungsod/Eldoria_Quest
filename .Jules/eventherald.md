## 2026-03-03 — Location-Specific Event Modifiers

**Learning:** Implementing location-specific event modifiers (like increased loot only in Frostfall) requires passing `location_id` through `AdventureSession.simulate_step` down to `AdventureRewards.process_victory` and `_process_loot_and_quests`, as `AdventureRewards` is initialized without location context.
**Action:** Ensure future event implementations that rely on location context update the reward processing pipeline to include `location_id`.

## 2026-02-28 — Global Modifiers via Active Boosts

**Learning:** Global event modifiers are processed and attached as `active_boosts` inside the session context in `_fetch_session_context()`. We can directly leverage these without adding separate logic layers inside `simulate_step`.
**Action:** Always check `context["active_boosts"]` for cleanly accessing currently active event modifiers.
