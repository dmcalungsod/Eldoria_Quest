## 2025-05-18 — Wild Gathering Mechanic
**Learning:** Adventure games often have "dead turns" where nothing happens. Turning these into small, random rewards (like gathering materials) keeps player engagement high without disrupting balance.
**Action:** When designing exploration loops, always add a low-probability fallback event that gives a small reward instead of "nothing found".

## 2025-05-23 — JSON Content Validation
**Learning:** The quest system relies on exact string matching for Monster Names and Item Names in `quests.json`, not internal IDs. There is no build-time validation for this.
**Action:** Always write a specific test case when adding new content to JSON files to verify that referenced entities (monsters, items) actually exist and names match exactly.
