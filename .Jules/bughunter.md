## 2026-02-27 — Fix Adventure Retreat Exploit

**Learning:** Players were able to exploit the "Retreat Early" button to escape active combat without penalty, keeping all loot. This broke the risk/reward loop of the Auto-Adventure system.
**Action:** Implemented a check in `AdventureManager.end_adventure` to detect if `active_monster` is present. If so, a 25% penalty is applied to gathered materials (Emergency Extraction). This logic is now enforced on the backend regardless of UI.
