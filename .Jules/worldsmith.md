## 2024-10-27 — Deterministic Weather Implementation

**Learning:** Python's built-in `hash()` function is randomized per process (due to hash randomization security features), making it unsuitable for generating consistent world states (like weather) across server restarts or distributed instances.
**Action:** Use `zlib.adler32(string.encode())` combined with a time seed (e.g., current hour) to generate stable, deterministic hash values for game world calculations. This ensures all players see the same weather in the same location at the same time.

## 2026-02-28 — Environmental Combat Integration

**Learning:** Dynamic systems (like Weather) feel most impactful when they alter core mechanics (damage types, turn events) rather than just passive encounter rates. Hooking directly into `CombatEngine` allows for emergent gameplay (e.g., avoiding Fire skills in Rain).
**Action:** When designing future systems (e.g., Seasons), prioritize deep integration into `CombatEngine` or `DamageFormula` over simple probability adjustments.

## 2026-03-04 — Dynamic Time/Weather Events

**Learning:** It is crucial to ensure variables derived from system state like `time_phase` and `weather` can trickle down appropriately through object and event handling pipelines (`AdventureSession` -> `EventHandler` -> `ExplorationEvents`) for a fully immersive implementation of condition-based events.
**Action:** Keep these context variables easily accessible from lower-level functions so that individual classes or utility functions can cleanly leverage conditions without making multiple repeated system time calls and violating atomic rules.

## 2026-03-12 — Weather Location Weights
**Learning:** Adding new adventure locations without updating their specific `LOCATION_WEATHER_WEIGHTS` in `game_systems/core/world_time.py` causes them to fall back to generic clear/rain combinations, limiting regional immersion and failing to meet dynamic weather expectations.
**Action:** When adding or verifying locations, ensure explicit entries exist in `world_time.py` for weather weighting.
