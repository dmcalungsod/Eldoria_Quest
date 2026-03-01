## 2024-10-26 — Migrated Quests to JSON

**Learning:** Migrating hardcoded Python tuples to structured JSON makes data much easier to read and maintain, but requires careful updates to all consumers (tests, database population, and runtime systems) to handle the change from index-based access to key-based access.
**Action:** When migrating data, always check for implicit assumptions about data types (e.g., JSON strings vs objects) in consumer code and update them to be robust.

## 2024-10-31 — Migrated Monsters to JSON

**Learning:** Migrating procedural Python monster generation to static JSON improves maintainability but requires careful hydration of related objects (skills) and conversion of types (lists to tuples for drops) to maintain backward compatibility.
**Action:** Use intermediate scripts to extract complex data structures from Python code into JSON, and ensure the loading layer handles type reconstruction to keep the external API consistent.

## 2026-03-01 — Centralizing Factions Data

**Learning:** Static data like `FACTIONS` was previously hardcoded in `game_systems/data/factions.py` without schema validation, increasing the risk of inconsistent data entry for future updates.
**Action:** Extracted faction data to `game_systems/data/factions.json` and implemented a `FACTION_SCHEMA` in `schemas.py`. Python files should act as loaders and validators, keeping data decoupled from logic. Ensure `ranks` keys are cast back to integers during load for backward compatibility.
