## 2026-03-07 — Alchemist & Warrior Mechanics

**Learning:** When mocking `PlayerStats` in unit tests, ensuring `max_hp` and `max_mp` are explicitly set (or mocked via property) is crucial, as `from_dict` internally recalculates these based on base stats (END/MAG), which can override simple mocked attribute assignments if not handled carefully.
**Action:** When testing subsystems that rely on `PlayerStats` (like `ConsumableManager`), verify if `max_hp` logic is derived or static, and mock the class instantiation itself (`patch('...PlayerStats')`) if precise control over derived properties is needed to match test case values.
