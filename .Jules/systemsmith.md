## 2026-03-09 — Refactoring ConsumableManager

**Learning:** Large handler functions in `ConsumableManager.use_item` can hit cyclomatic complexity values as high as 39, hindering maintainability.
**Action:** Extract logic into explicitly separated methods for input validation (`_verify_consumable_data`), passive skill computation (`_get_healing_multiplier`), specific effect handling (`_apply_healing` and `_apply_mana`), and buffering and side effects (`_process_buffs`). This pattern can consistently map single-function "God Methods" down to C-grade or lower values reliably.
