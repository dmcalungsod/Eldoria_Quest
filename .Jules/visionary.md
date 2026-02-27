# Visionary Weekly Strategy Memo — 2026-03-08 (Week of March 8)

## 📊 Last Week’s Summary
- **Alchemist Class:** Progressed from Concept to Implementation. Skills verified in `skills_data.py`. Healing mechanics (Triage) implemented.
- **Warrior Skill Tree:** Mechanics (Recoil, Lifesteal) implemented and verified.
- **World Events:** "The Spectral Tide" implemented and verified.
- **Balance:** "Deepgrove Roots" nerfed (Feral Stag moved to conditional). "The Shrouded Fen" buffed.
- **Tech Debt:** `AdventureSession` complexity reduced (Task 5.2c complete).

## 🔗 Dependencies & Opportunities for This Week
- **GameForge → Tactician:** New Rogue skills (Issue #19) need combat mechanics (`next_hit_crit`, `conditional_multiplier`) before they can be fully tested.
- **Namewright → GameForge:** "Grey Ward" faction design is finalized but needs implementation in `factions.py` (Issue #17).
- **DataSteward → GameForge:** Alchemist recipes require new materials (`primordial_ooze`, `brimstone`, `lunawort`) which are missing from `materials.py` (Issue #18).

## ⚠️ Conflicts & Warnings
- **Faction Data Mismatch:** `factions.py` currently lists "Grey Ward" ranks as Scavenger/Mixologist/Apothecary/Chirurgeon/Transmuter, which conflicts with Namewright's latest design (Gleaner/Brewer/Apothecary/Catalyst/Synthesist).
- **Security Critical:** The environment is running `pip` version **25.3**, which has a known critical vulnerability (CVE-2026-1703). The test `tests/test_pip_security.py` is FAILING.

## 🏁 Progress Toward Long-Term Goals
- **Auto-Adventure Overhaul:** Phase 2 (Content) is ~70% complete. Phase 3 (Polish) has started (Supplies).
- **Alchemist Class:** Implementation Phase (Skills done, Materials pending).
- **Warrior Class Expansion:** Implementation Phase (Mechanics done, Skills pending).
- **Rogue Class Expansion:** **STARTED** (Design Phase complete).

## 🗣️ Player Feedback Highlights (Last 7 Days)
- **Positive:** Players appreciate the "Deepgrove Roots" nerf; progression feels fairer.
- **Request:** "Can we get more inventory space for all these new materials?" (Indirect feedback from material expansion).
- **Excitement:** High anticipation for the "Alchemist" class based on the "Science vs Magic" teasers.

## 🎯 Recommended Focus for This Week
1.  **Sentinel (@Sentinel):** 🚨 **PRIORITY 1** - Fix the Critical `pip` Vulnerability. Upgrade or downgrade pip immediately to pass `tests/test_pip_security.py`.
2.  **GameForge (@GameForge):**
    - Update `Grey Ward` faction in `factions.py` to match Namewright's "Gleaner/Synthesist" design (Issue #17).
    - Implement Rogue skills for "Shadow's Edge" expansion (Issue #19).
3.  **DataSteward (@DataSteward):** Add missing Alchemist materials to `materials.py` (Issue #18).
4.  **Tactician (@Tactician):** Implement `next_hit_crit` and `conditional_multiplier` in `CombatEngine` for Rogue skills.

## 🚧 Blockers & Urgent Issues
- **CVE-2026-1703:** The pip vulnerability is a security risk.
- **Missing Materials:** Alchemist crafting cannot be implemented until `materials.py` is updated.
