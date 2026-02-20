## 2024-10-27 — Deterministic Weather Implementation

**Learning:** Python's built-in `hash()` function is randomized per process (due to hash randomization security features), making it unsuitable for generating consistent world states (like weather) across server restarts or distributed instances.
**Action:** Use `zlib.adler32(string.encode())` combined with a time seed (e.g., current hour) to generate stable, deterministic hash values for game world calculations. This ensures all players see the same weather in the same location at the same time.
