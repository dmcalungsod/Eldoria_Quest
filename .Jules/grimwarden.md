## 2026-03-01 — Enforcing the Grimwarden's Toll

**Learning:** Discovered that the initial implementation of the auto-adventure death penalty in `adventure_manager.py` did not align with the strict "Grimwarden's Toll" specs outlined in the design document (`timeweaver_design.md`). Specifically, the material loss was only 50% (instead of 100%), the aurum penalty was 10% (instead of 5%), and allocated supplies were not being lost upon death. A half-measure on death penalties reduces the survival tension that makes Eldoria Quest engaging.

**Action:** Enforced strict adherence to the design spec by updating `adventure_manager.py` to completely wipe session loot and supplies on death, while reducing the baseline Aurum penalty to 5%. This aligns the consequence of failure with the intended dark survival tone without being overwhelmingly punishing on permanent wealth. Updated associated regression tests to assert 100% loss. Next time, always cross-reference completed assignments against the primary design spec for accurate realism enforcement.

## 2026-03-02 — Sensory Deprivation Mechanics in Ouros

**Learning:** Implemented sensory deprivation mechanics for the new 'Silent City of Ouros' region. Found that checking location ID during environmental effect resolution (`_apply_sanity_drain`) and fatigue calculation (`_calculate_fatigue_multiplier`) provides an effective hook to introduce region-specific realism mechanics. Re-using the MP drain mechanic but with tailored flavor text fit well with the existing Wailing Chasm implementation.

**Action:** Adjusted `adventure_session.py` to double fatigue scaling and apply MP drain within Ouros. When building future region-specific realism mechanics, utilizing the core loops in `simulate_step` and `_fetch_session_context` continues to be the most robust approach.
