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
