## 2026-03-07 — Alchemist & Warrior Mechanics

**Learning:** When mocking `PlayerStats` in unit tests, ensuring `max_hp` and `max_mp` are explicitly set (or mocked via property) is crucial, as `from_dict` internally recalculates these based on base stats (END/MAG), which can override simple mocked attribute assignments if not handled carefully.
**Action:** When testing subsystems that rely on `PlayerStats` (like `ConsumableManager`), verify if `max_hp` logic is derived or static, and mock the class instantiation itself (`patch('...PlayerStats')`) if precise control over derived properties is needed to match test case values.

## 2026-03-02 — Phase 5 Tech Debt & Wailing Chasm Setup

**Learning:** When writing to large JSON dictionaries in the Eldoria Quest codebase containing rich text descriptions and emojis (e.g. `adventure_locations.json`), `json.dump()` must be called with `ensure_ascii=False` to avoid converting emojis and unicode characters into escape sequences and making the raw file less legible. Furthermore, when migrating key schemas like `"buff_data"` to `"buff"`, it's critical to write access logic defensively with fallbacks like `skill.get("buff", skill.get("buff_data", {}))` to not silently break components or external mods injecting older data.
**Action:** Always maintain backward compatibility on data schema renames and always remember to use `ensure_ascii=False` when updating JSON files to protect existing emoji configurations.
