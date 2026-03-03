# Expansion Blueprint: Guild Halls (Player Housing & Shared Resources)

## 🏰 Concept
"Even in the dark, a hearth must burn."
The Guild Halls expansion introduces instanced, upgradable player housing and shared guild spaces to Eldoria Quest. This serves as a massive long-term material sink, a way to display achievements (tying into the Codex system), and a strategic hub that provides passive benefits to preparation and recovery.

## 📜 Lore (for StoryWeaver)
As Astraeon expands its secure perimeters deeper into the Wilds, the Adventurer's Guild has begun reclaiming abandoned strongholds and manors from before the Sundering. These properties are leased to distinguished adventurers and registered companies. They are not merely homes; they are fortified forward operating bases, alchemical laboratories, and monuments to those who have carved safety out of chaos.

## 🏗️ Core Mechanics

### 1. Acquisition & Upkeep
*   **The Deed:** Players can purchase a "Dilapidated Manor Deed" once they reach Guild Rank C. The base cost is steep (e.g., 50,000 Aurum + 500 Stone + 500 Wood).
*   **Upkeep:** A weekly tax in Aurum or raw materials. Failing to pay disables passive buffs until the debt is cleared, but the property is never lost.

### 2. Upgradable Rooms (The Strategic Hub)
Halls are modular. Players spend materials (Wood, Stone, Iron, specialized drops) to build and upgrade rooms:
*   **The Hearth (Core):** Determines the max level of other rooms. Upgrading requires rare boss drops (e.g., *Smoldering Core*).
*   **The Infirmary:** Reduces the "Rest Period" penalty between consecutive auto-adventures. Higher levels grant a small starting HP shield for the next expedition.
*   **The Apothecary (Alchemist synergy):** Slowly generates basic potions over time, or increases the yield when crafting consumables.
*   **The Armory:** Increases the maximum durability or charges of equipped items (if durability is ever implemented), or provides a flat 1% to 3% damage buff to all weapons stored/displayed here.

### 3. Display & Trophies (Codex Synergy)
*   **Trophy Room:** Players can craft trophies from the "Mastered" tier bosses in their Bestiary (e.g., *Stuffed Feral Stag Head*, *Void Wraith Core Pedestal*).
*   **The Vault:** A place to visually display fully completed item sets from the Armory. Displaying a set grants its cosmetic profile badge to all members of the Hall.

### 4. Shared Guild Spaces (Future Multiplayer)
*   If a player is the leader of a registered "Company" (multiplayer guild), their Hall becomes the Company Hall.
*   Members can pool resources to build rooms.
*   The Infirmary/Apothecary buffs apply to all active members.

## 🔗 Integration Notes & Task Allocation

### 🛠️ For DataSteward & SystemSmith
1.  **Database:** Create a `player_halls` collection to track ownership, room levels, and stored trophies.
2.  **Schema:** Needs to support modular upgrades (`{ "infirmary_level": 2, "apothecary_level": 0 }`).

### ⚖️ For GameBalancer
1.  **Economy Sink:** Ensure the material costs for upgrades scale exponentially to drain excess mid-tier materials (e.g., iron, silk, common monster parts).
2.  **Buff Tuning:** The passive buffs from rooms must be meaningful but not break the combat engine. (e.g., Infirmary shield should be max 5% of HP).

### 🎨 For Palette (UI/UX)
1.  **One UI Policy:** The Guild Hall should be a persistent, tabbed View (similar to the Profile or Codex) where players can navigate rooms, see required materials, and click `[Upgrade]` or `[Deposit]`.
2.  **Visuals:** ASCII or emoji-based visual representation of the Hall's current state would be highly engaging.

### 🔨 For GameForge
1.  **New Items:** Create "Building Materials" (Refined Stone, Treated Lumber) that are crafted from raw materials gathered in the Wilds.
2.  **Trophy Items:** Add specific rare drops to Rank A and S bosses that have no purpose other than crafting Trophies.

## 📈 Timeline & Success Criteria
*   **Phase 1 (Foundation):** Deed acquisition, basic UI, and The Hearth upgrade path.
*   **Phase 2 (Utility):** Infirmary and Apothecary functional with integration into `AdventureSession` rest mechanics.
*   **Phase 3 (Vanity):** Trophy Room and Codex integration.
*   **Success Metric:** 30% of Rank C+ players purchasing a Deed within the first two weeks; a noticeable deflation in common material stockpiles.
