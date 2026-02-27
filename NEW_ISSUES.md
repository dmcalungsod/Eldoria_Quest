# Issue Crafter: New Issues

**Title:** [Feature] Rogue Skill Tree Expansion ("Shadow's Edge")

**Description:**
- **Source:** Architect Design (`.Jules/architect_designs/skill_tree_rogue.md`) & Agent Log 2026-03-08
- **Details:** Implement the "Assassin" and "Phantom" skill paths for the Rogue class to differentiate playstyles.
- **Requirements:**
  - **Skills (GameForge):**
    - `double_strike` (Active, Tier 1): 2x hit, DEX scaling.
    - `stealth` (Passive, Tier 1): +10% AGI.
    - `toxic_blade` (Active, Tier 2): Weak hit + Poison.
    - `shadow_step` (Active, Tier 2): +Evasion, `next_hit_crit` buff.
    - `venomous_strike` (Active, Tier 3): Bonus dmg if target poisoned.
    - `flash_powder` (Active, Tier 3): AoE Blind (-Accuracy).
    - `death_blossom` (Ultimate, Rank A): AoE Damage + Bleed.
  - **Mechanics (Tactician):**
    - Implement `next_hit_crit` flag in `CombatEngine` (guarantees crit on next attack).
    - Implement `conditional_multiplier` in `DamageFormula` (check `target_poisoned`).
    - Implement `accuracy_percent` debuff logic in `MonsterAI` or `DamageFormula`.
  - **Achievements (ChronicleKeeper):**
    - Title: "Assassin" (Unlock Assassin path).
    - Title: "Phantom" (Unlock Phantom path).
    - Achievement: "Unseen Death" (Win battle w/o taking damage as Rogue).
- **Labels:** `feature`, `class-rogue`, `mechanics`
- **Assignee:** @GameForge, @Tactician
