## 2024-10-26 — Migrated Quests to JSON

**Learning:** Migrating hardcoded Python tuples to structured JSON makes data much easier to read and maintain, but requires careful updates to all consumers (tests, database population, and runtime systems) to handle the change from index-based access to key-based access.
**Action:** When migrating data, always check for implicit assumptions about data types (e.g., JSON strings vs objects) in consumer code and update them to be robust.

## 2024-10-31 — Migrated Monsters to JSON

**Learning:** Migrating procedural Python monster generation to static JSON improves maintainability but requires careful hydration of related objects (skills) and conversion of types (lists to tuples for drops) to maintain backward compatibility.
**Action:** Use intermediate scripts to extract complex data structures from Python code into JSON, and ensure the loading layer handles type reconstruction to keep the external API consistent.
