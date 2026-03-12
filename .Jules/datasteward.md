## 2024-10-26 — Migrated Quests to JSON

**Learning:** Migrating hardcoded Python tuples to structured JSON makes data much easier to read and maintain, but requires careful updates to all consumers (tests, database population, and runtime systems) to handle the change from index-based access to key-based access.
**Action:** When migrating data, always check for implicit assumptions about data types (e.g., JSON strings vs objects) in consumer code and update them to be robust.

## 2024-10-31 — Migrated Monsters to JSON

**Learning:** Migrating procedural Python monster generation to static JSON improves maintainability but requires careful hydration of related objects (skills) and conversion of types (lists to tuples for drops) to maintain backward compatibility.
**Action:** Use intermediate scripts to extract complex data structures from Python code into JSON, and ensure the loading layer handles type reconstruction to keep the external API consistent.

## 2026-03-01 — Centralizing Factions Data

**Learning:** Static data like `FACTIONS` was previously hardcoded in `game_systems/data/factions.py` without schema validation, increasing the risk of inconsistent data entry for future updates.
**Action:** Extracted faction data to `game_systems/data/factions.json` and implemented a `FACTION_SCHEMA` in `schemas.py`. Python files should act as loaders and validators, keeping data decoupled from logic. Ensure `ranks` keys are cast back to integers during load for backward compatibility.

## 2026-03-03 — Migrated Skills to JSON

**Learning:** Centralizing class skills from Python dictionaries into `skills.json` and adding a formal `SKILL_SCHEMA` ensures skill integrity at startup and prevents typos from breaking the combat engine. Using PEP 562 `__getattr__` allows lazy loading without breaking external imports.
**Action:** Continue identifying large hardcoded dictionaries (like class stats or descriptions) and extracting them into structured JSON files with schema validation.

## 2026-03-13 — Designing Codex System Data Schemas

**Learning:** When expanding data systems like the Codex, it's essential to define robust validation schemas in `schemas.py` that match the expected JSON structure in `codex.json`. Incorporating required nested dictionaries (like `unlock_thresholds`) ensures that systems relying on this data won't encounter `KeyError`s during runtime.
**Action:** When creating new static data features, always co-develop the JSON data structure alongside a strict Pydantic or custom schema definition, and provide a migration template for existing entities (monsters, items, locations).

## 2026-03-14 — Implemented `player_halls` Database Schema

**Learning:** When expanding major features like the Guild Halls, establishing the underlying database schema early is crucial. Leaving it out causes dependency chains to break when other agents try to integrate their components (like items or costs).
**Action:** Created the `player_halls` database collection, added it to `INDEX_DEFINITIONS` in `create_database.py`, and established the primary CRUD operations (`get_player_hall`, `create_player_hall`, `update_player_hall_room`, `add_player_hall_trophy`) in `DatabaseManager` to unblock further development for the expansion.

## 2026-03-14 — Fixed Missing Materials for The Undergrove

**Learning:** Missing materials or monsters in the data dictionary for new regions can cause severe economy disruptions and reward cliffs (like the -96.0% EV drop in The Undergrove reported by the Analyst).
**Action:** When game designers create new locations, verify all associated `gatherables` and `monsters` strings explicitly map to existing IDs in `materials.json` and `monsters.json` respectively.
