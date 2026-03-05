## 2026-03-09 — Refactoring ConsumableManager

**Learning:** Large handler functions in `ConsumableManager.use_item` can hit cyclomatic complexity values as high as 39, hindering maintainability.
**Action:** Extract logic into explicitly separated methods for input validation (`_verify_consumable_data`), passive skill computation (`_get_healing_multiplier`), specific effect handling (`_apply_healing` and `_apply_mana`), and buffering and side effects (`_process_buffs`). This pattern can consistently map single-function "God Methods" down to C-grade or lower values reliably.

## 2026-03-10 — Cyclomatic Complexity Refactor
**Learning:** Heavy reliance on giant try/except blocks inside `equip_item` and `use_item` creates unmanageable cyclomatic complexity. Extracting validations, resolutions, and transactions into discrete private methods makes code testable and lowers cognitive load.
**Action:** Standardize on breaking down major state-changing interactions into at least three phases: Validation -> Conflict Resolution -> DB Transaction.

## 2026-03-10 — Refactoring equip_loadout Cyclomatic Complexity
**Learning:** `EquipmentManager.equip_loadout` was overly complex (C 18) due to iterating through `items_to_equip.items()` and looking for a match in inventory, and falling back to checking if the item is already equipped, all within the same method.
**Action:** Extracting this matching and equipping logic into a dedicated helper method `_equip_loadout_item` significantly reduces the complexity of the main function, making it easier to read and test.
