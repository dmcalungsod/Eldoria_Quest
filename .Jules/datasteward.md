## 2024-10-26 — Migrated Quests to JSON

**Learning:** Migrating hardcoded Python tuples to structured JSON makes data much easier to read and maintain, but requires careful updates to all consumers (tests, database population, and runtime systems) to handle the change from index-based access to key-based access.
**Action:** When migrating data, always check for implicit assumptions about data types (e.g., JSON strings vs objects) in consumer code and update them to be robust.
