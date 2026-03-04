## 2024-05-22 — The Molten Caldera

**Learning:** High-rank players (Rank A) lacked a dedicated challenge zone after the Crystal Caverns (Rank B). Vertical progression was capped at Level 20 content, leaving a gap for Level 30+ growth.
**Action:** Implemented "The Molten Caldera" (Rank A, Level 30+).
- **Theme:** Elemental Fire / Volcanic.
- **Mechanics:** Introduced `ATMOSPHERE_MAGMA` for environmental immersion.
- **Economy:** Added `obsidian_shard`, `fire_essence`, `magma_core`, and `dragon_scale` to support future crafting tiers.
- **Challenge:** Designed "Ignis, Lord of Cinders" as a high-HP boss to test sustain and DPS.

## 2025-10-28 — The Void Sanctum

**Learning:** Rank A content was the ceiling, with no endgame for Rank S players. Vertical progression stalled at Level 30-35.
**Action:** Implemented "The Void Sanctum" (Rank S, Level 40+).
- **Theme:** Void / Entropy / Cosmic Horror.
- **Mechanics:** Introduced high-damage physical/magical hybrids (Void Slash, Entropy Wave).
- **Economy:** Added `void_dust`, `abyssal_shackle`, `entropy_crystal`, `null_stone`, and `void_heart` (Epic).
- **Challenge:** Designed "Omega, The Void Heart" (Level 45 Boss) with an "Annihilate" ultimate skill to test mitigation.

## 2025-10-29 — The Clockwork Halls

**Learning:** Players felt a progression gap between Rank B (Level 20) and Rank A (Level 25+). The jump from "Crystal Caverns" to "Frostfall Expanse" was steep.
**Action:** Implemented "The Clockwork Halls" (Rank B, Level 22).
- **Theme:** Steampunk / Ancient Machinery.
- **Mechanics:** Introduced `ATMOSPHERE_CLOCKWORK` for immersive audio-visual cues (grinding gears, steam).
- **Economy:** Added `brass_gear`, `copper_wire`, `spring_coil`, `steam_core`, and `clockwork_heart` to support mid-tier crafting.
- **Challenge:** Designed "The Gear Warden" (Level 26 Boss) with `steam_vent` to test magical mitigation.

## 2025-10-30 — Exploration Events

**Learning:** Exploration felt repetitive, consisting mainly of combat or generic gathering. Players lacked meaningful non-combat interactions that offered risk/reward choices.
**Action:** Implemented the `ExplorationEvents` system.
- **Mechanics:** Added 15% chance for special events: Safe Rooms (Heal), Hidden Stashes (Loot), Ancient Shrines (XP), and Traps (Damage).
- **Immersion:** Added unique flavor text for each event type.
- **Progression:** Provided alternative ways to sustain runs (Healing) or gain resources (Loot/XP) outside of combat.

## 2026-02-23 — Gale-Scarred Heights

**Learning:** Players faced a steep difficulty spike between Rank A (Level 30) and Rank S (Level 40). A bridge was needed at Level 35.
**Action:** Implemented "Gale-Scarred Heights" (Rank A, Level 35).
- **Theme:** High altitude / Wind / Storm.
- **Mechanics:** Introduced wind-themed skills (`gust`, `aerial_dive`, `thunder_call`) focusing on magic/physical hybrid damage.
- **Economy:** Added `cloud_wisp`, `griffon_feather`, `charged_core`, and `tempest_heart` to support future crafting.
- **Challenge:** Designed "Tempest Guardian" (Level 39 Boss) with `aerial_dive` and `thunder_call` to test mixed mitigation.

## 2026-03-05 — The Grey Ward

**Learning:** Players interested in alchemy and survival had no dedicated faction to align with, despite lore references.
**Action:** Implemented "The Grey Ward" faction.
- **Identity:** Alchemists and pragmatists who study The Rot and use corruption to survive.
- **Progression:** Ranks from Gleaner to Master Apothecary.
- **Rewards:** Utility consumables (`bitter_panacea`, `phial_of_vitriol`) and gathering buffs.
- **Integration:** Favored locations include `whispering_thicket` and `deepgrove_roots`, encouraging exploration of corrupted zones.

## 2026-03-01 — The Grey Ward Update

**Learning:** Coordinated with Namewright design to adjust Grey Ward progression.
**Action:** Updated ranks (Gleaner to Synthesist) and adjusted crafting reputation values.

## 2026-03-02 — Deep Floor Unlock System

**Learning:** Deep floor access should be gated behind narrative or gameplay prerequisites to enforce vertical progression, rather than strictly relying on Rank and Level requirements alone. This adds depth to the exploration loop and makes reaching deeper floors feel like a genuine accomplishment.
**Action:** Implemented the `prerequisite_location` field in `adventure_locations.json`. Linked "The Silent City of Ouros" to "The Void Sanctum" meaning players must have visited The Void Sanctum before they can enter Ouros. Updated the `AdventureSetupView` to check for this prerequisite.

## 2026-03-04 — The Abyssal Descent

**Learning:** The Void Sanctum and Silent City of Ouros lacked a transitional zone. Floor 41 was created to connect them properly per Foreman's plan.
**Action:** Add intermediate zones when major thematic changes occur between deep floors.
