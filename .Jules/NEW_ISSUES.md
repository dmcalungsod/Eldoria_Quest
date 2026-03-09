**Title:** [Feature] Implement Guild Halls Expansion (Player Housing & Shared Resources)

**Description:**
- **Source:** Architect log 2026-03-02
- **Details:** Add instanced, upgradable player housing and shared guild spaces as a long-term material sink. Includes core mechanics (Deed acquisition at Rank C, upkeep), upgradable rooms (The Hearth, Infirmary, Apothecary, Armory), Trophy Room, and The Vault.
- **Acceptance criteria:**
  - `player_halls` collection created to track ownership and rooms.
  - "Building Materials" (Refined Stone, Treated Lumber) and boss trophies added to crafting/drops.
  - Exponential material costs tuned for room upgrades.
  - Interactive Guild Hall management View (One UI Policy) designed.
- **Labels:** `enhancement`, `content`, `guild`
- **Assignee:** @DataSteward, @SystemSmith, @GameBalancer, @GameForge, @Palette

---

**Title:** [Feature] Implement Ironhaven Region Mechanics & Content

**Description:**
- **Source:** Realmwright log 2026-03-03
- **Details:** Add the new Rank A fortified mountain city region, Ironhaven. Features Cold and Altitude exploration mechanics, new monsters (Storm Drakes, Iron-clad Trolls, Frost Gargoyles), resources (Star Metal, Frost-forged Steel, Drake Scales, Glacial Hearts), and new quests ("The Sky is Falling", "The Broken Anvil").
- **Acceptance criteria:**
  - New monsters and resources added to `monsters.json` and `materials.json`.
  - Cold and Altitude survival mechanics implemented (e.g., thermal gear requirement, stamina drain).
  - New storyline quests added to `quests.json`.
  - Atmospheric flavor text added.
  - Dungeons connected beneath the Deep Forges.
- **Labels:** `enhancement`, `content`, `region`
- **Assignee:** @GameForge, @Grimwarden, @StoryWeaver, @Tactician, @DepthsWarden, @GameBalancer, @ProgressionBalancer, @ChronicleKeeper, @Equipper, @Namewright

---

**Title:** [Bug] Fix missing discord mock in test_guild_advisor.py

**Description:**
- **Source:** Jules log 2026-03-03
- **Steps to reproduce:** Run `test_guild_advisor.py` without Discord imports available (or in isolated test environment).
- **Expected behavior:** Test passes using mocked `discord` module.
- **Actual behavior:** Test fails due to a missing mock of the `discord` module when testing without imports.
- **Suggested fix:** Add `sys.modules['discord'] = MagicMock()` or patch `discord` in `test_guild_advisor.py`.
- **Labels:** `bug`, `testing`
- **Assignee:** @BugHunter

---

**Title:** [Test] Verify AdventureSetupView for new players

**Description:**
- **Source:** Mentor log 2026-03-09
- **Details:** Ensure that new players with 0 expeditions interacting with the `AdventureSetupView` (which now has context-aware Mentor advice) pass without issue.
- **Acceptance criteria:**
  - Automated or manual tests verify the new player expedition flow in `adventure_menu.py`.
- **Labels:** `bug`, `testing`, `ui`
- **Assignee:** @BugHunter

---

**Title:** [Feature] Add thermal insulation gear for Ironhaven

**Description:**
- **Source:** Grimwarden log 2026-03-09
- **Details:** The new Ironhaven region has cold and altitude mechanics that deal damage unless the player has gear with `thermal_insulation`.
- **Acceptance criteria:**
  - New equipment (or modifications to existing) added to grant the `thermal_insulation` property.
- **Labels:** `enhancement`, `content`, `equipment`
- **Assignee:** @Equipper

---

**Title:** [Feature] Implement The Undergrove Region Mechanics & Content

**Description:**
- **Source:** Realmwright log 2026-03-09
- **Details:** Add the new subterranean jungle region, The Undergrove. Features glowing, toxic environments, new 'Toxin' accumulation mechanics, new monsters (Fungal Hulks, Spore-Stalkers), resources (Lunawort, Primordial Ooze), and specific achievements.
- **Acceptance criteria:**
  - Monsters and resources implemented.
  - Toxin accumulation and poison-stacking mechanics balanced and implemented.
  - Atmospheric descriptions added.
  - Respirator Masks and Purifying Brews designed.
  - Dungeon connections established.
  - Flora/tool names finalized.
  - Rank B validation and economy evaluation completed.
  - Achievements added.
- **Labels:** `enhancement`, `content`, `region`
- **Assignee:** @GameForge, @StoryWeaver, @Grimwarden, @Tactician, @GameBalancer, @Equipper, @DepthsWarden, @Namewright, @ProgressionBalancer, @ChronicleKeeper

---

**Title:** [Feature] Add player_halls database implementation for Building Materials

**Description:**
- **Source:** Artisan log 2026-03-11
- **Details:** Building Materials (`refined_stone`, `treated_lumber`) and Boss Trophies (`stuffed_feral_stag_head`, `void_wraith_core_pedestal`) have been implemented. The associated `player_halls` database implementation is now needed, and GameBalancer should verify the costs fit exponential models.
- **Acceptance criteria:**
  - Database schema for `player_halls` is ready.
  - GameBalancer confirms the exponential models.
- **Labels:** `enhancement`, `database`, `guild`
- **Assignee:** @DataSteward, @SystemSmith, @GameBalancer

---

**Title:** [Balance] Progression Gaps identified in several locations

**Description:**
- **Source:** Analyst log 2026-03-14
- **Details:** Analyst confirmed critical EV drops in The Crystal Caverns (-40.6%), The Forgotten Ossuary (-79.6%), The Molten Caldera (-80.4%), and Gale-Scarred Heights (-59.9%).
- **Acceptance criteria:**
  - GameBalancer addresses the progression gaps.
- **Labels:** `balance`, `economy`, `priority-high`
- **Assignee:** @GameBalancer

---

**Title:** [Bug] Missing description for howling_peaks

**Description:**
- **Source:** Analyst log 2026-03-14
- **Details:** Analyst confirmed that `howling_peaks` is missing its `description`.
- **Acceptance criteria:**
  - Add `description` to `howling_peaks`.
- **Labels:** `bug`, `data`, `priority-high`
- **Assignee:** @GameForge, @DataSteward

---

**Title:** [Bug] Missing skills for frost_gargoyle and storm_drake

**Description:**
- **Source:** Analyst log 2026-03-14
- **Details:** Analyst confirmed that `frost_gargoyle` and `storm_drake` still reference missing skills (`ice_spear`, `dragon_breath`, and `whirlwind`).
- **Acceptance criteria:**
  - Implement missing skills: `ice_spear`, `dragon_breath`, and `whirlwind`.
- **Labels:** `bug`, `data`, `priority-high`
- **Assignee:** @GameForge, @DataSteward
