# Expansion Blueprint: The Survival & Logistics Update

## 🏕️ Concept
Eldoria is not just a battleground; it is a harsh, unforgiving world where the environment itself is an enemy. The "Survival & Logistics Update" introduces systems that make **preparation** as critical as combat prowess.

This update transforms long-duration adventures from "set and forget" into strategic choices. Players must manage **Fatigue**, counteract **Regional Hazards**, and pack the right **Supplies** to survive the deep wilderness.

## 📜 Lore Hook (for StoryWeaver)
> "The Veil didn't just break the world; it broke the seasons. The Frostfall winds strip warmth from your bones in minutes, and the Caldera's heat boils potion in the flask. To venture beyond the walls of the Citadel without preparation is to invite a quiet, cold death."
> — *Garrick, Master of the Guild Supply Corps*

---

## ⚙️ Core Systems

### 1. The Fatigue System (Task 2.3)
**Goal:** Introduce a soft cap on adventure duration to encourage strategic rests and supply usage.

**Mechanics:**
*   **Threshold:** Fatigue begins to accumulate after **4 hours** (16 steps) of continuous adventuring.
*   **Penalty:** Monsters gain **+5% Damage** and **+2% Crit Chance** for every hour past the threshold.
    *   *Example:* A 6-hour adventure sees +10% Damage / +4% Crit in the final hour.
*   **Cap:** Maximum penalty is +50% Damage / +20% Crit (at 14 hours).
*   **Recovery:** Completing an adventure resets Fatigue.
*   **Mitigation:**
    *   **Supplies:** `Hardtack` reduces fatigue accumulation rate by 20%.
    *   **Events:** "Safe Room" events can reduce current Fatigue by 1 hour.

### 2. Regional Hazards (New)
**Goal:** Make high-level regions feel distinct and dangerous, requiring specific preparation.

**Hazard Types:**
| Region | Hazard | Effect | Mitigation |
| :--- | :--- | :--- | :--- |
| **Frostfall Expanse** | **Bone-Chilling Cold** | -10% Max HP (Frostbite) per hour. | **Fur-Lined Cloak** (Item) or **Warming Stone** (Supply). |
| **The Molten Caldera** | **Oppressive Heat** | +20% Stamina Cost for Skills. Potions heal 20% less. | **Cooling Salve** (Supply) or **Hydration Pack** (Item). |
| **The Void Sanctum** | **Abyssal Whisper** | -5% Max MP (Sanity Loss) per hour. | **Warding Talisman** (Item) or **Sanity Incense** (Supply). |

**Implementation:**
*   Hazards are "Passive Debuffs" applied at the start of an adventure in these regions.
*   Mitigation items in inventory (passive) or supplies (consumable) negate or reduce these effects.

### 3. Expanded Supply System (Task 3.3)
**Goal:** Give players agency over adventure outcomes through loadout choices.

**New Item Category:** `supply`
*   Supplies are consumed automatically during adventures to trigger beneficial effects.
*   Players can equip up to **3 types** of supplies per adventure (Slots unlock at Ranks F, D, B).

**Supply List:**

| Item Name | Effect | Rarity | Cost/Recipe |
| :--- | :--- | :--- | :--- |
| **Hardtack** | Delays Fatigue onset by 1 hour. | Common | 50 Aurum / Cooking |
| **Pitch Torch** | Reduces Ambush chance by 50% in Night/Darkness. | Common | 30 Aurum / Crafting |
| **Climbing Kit** | Unlocks "Shortcut" events (skip 1 step, gain loot). | Uncommon | 150 Aurum / Crafting |
| **Bedroll** | Allows 1 "Rest" event (Restore 30% HP/MP) if HP < 50%. | Uncommon | 200 Aurum / Leatherworking |
| **Mapping Tools** | Increases chance of "Discovery" events (Rare Loot) by 15%. | Rare | 500 Aurum / Scribing |
| **Warming Stone** | Negates **Bone-Chilling Cold** for 4 hours. | Uncommon | Alchemy (Fire Essence) |
| **Cooling Salve** | Negates **Oppressive Heat** for 4 hours. | Uncommon | Alchemy (Frost Crystal) |
| **Sanity Incense** | Halves **Abyssal Whisper** drain. | Rare | Alchemy (Void Dust) |

---

## 🤝 Agent Coordination & Implementation

### 🛠️ For GameForge (Content)
1.  **Create Supply Items:** Add definitions to `consumables.json` for all new supplies.
2.  **Recipes:** Add crafting recipes for Bedroll, Climbing Kit, and Hazard mitigations.
3.  **Shop Update:** Add basic supplies (Hardtack, Torch) to the General Store.

### ⚔️ For Tactician (Systems)
1.  **Update `AdventureSession`:**
    *   Implement **Hazard Logic**: Check location ID -> Apply debuff to `PlayerStats` in `_fetch_session_context`.
    *   Implement **Supply Logic**:
        *   `Bedroll`: Check in `simulate_step`. If HP < 50% and not used, trigger "Rest" event.
        *   `Climbing Kit`: Add "Shortcut" to event pool.
        *   `Mapping Tools`: Increase weight of "Discovery" events.
2.  **Update `AdventureResolutionEngine`:**
    *   Ensure Fatigue calculations include the `Hardtack` modifier.

### 🎨 For Palette (UI)
1.  **Update `AdventureSetupView`:**
    *   Add a **"Select Supplies"** step before confirmation.
    *   Display current supply slots (1-3 based on Rank).
    *   Show warnings for Regional Hazards (e.g., "⚠️ Freezing Cold detected! Recommend: Warming Stone").

### ⚖️ For GameBalancer (Balance)
1.  **Tune Fatigue:** Verify that 4 hours is the right threshold. It should punish "AFK farming" without hurting casual 6-hour sessions too much.
2.  **Hazard Impact:** Ensure Hazards are dangerous but not instant killers. 10% HP/hour is significant—testing required.

### 📖 For StoryWeaver (Flavor)
1.  **Write Event Text:**
    *   *Rest (Bedroll):* "You unroll your bedding in a sheltered nook, recovering strength."
    *   *Shortcut (Climbing Kit):* "Using your ropes, you descend a sheer cliff, bypassing the winding path."
    *   *Cold Hazard:* "Your fingers numb, and your breath freezes in your lungs."

---

## 🧪 Success Criteria
1.  **Strategic Depth:** Players actively check region hazards and swap supplies (e.g., Torch for Night, Warming Stone for Frostfall).
2.  **Economy Sink:** Supplies create a constant, small drain on Aurum/Materials, balancing the economy.
3.  **Survival Feel:** The game feels more like an expedition, less like a spreadsheet.
