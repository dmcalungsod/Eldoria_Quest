# Class Design: Alchemist

## 🧪 Concept
A pragmatic survivor who views the Sundering not as a curse, but a chemical reaction to be understood. While Mages channel the Veil and Clerics pray to it, Alchemists bottle it. They use volatile mixtures to control the battlefield, stripping enemy defenses and turning the environment against them.

**Role:** Utility / DoT / Debuffer.
**Theme:** "Science in a world of Magic." Glass, fumes, and calculated risk.

## 📜 Lore (for StoryWeaver)
> "The gods didn't save us when the sky cracked. Steel rusted, and prayers went unanswered. But the rot... the rot was honest. It taught me that everything breaks down if you apply the right catalyst. I am not a hero; I am just the one who knows the formula for your undoing."
> — *Kaelen, First Alchemist of the Grey Ward*

Alchemists are often former scholars, apothecaries, or survivalists who realized that the warped mana of the world could be distilled into physical forms. They are respected for their ability to cure the incurable, but feared for their ability to liquefy armor.

## 📊 Base Stats (for GameBalancer)
*   **HP:** Medium (1.1x Rogue base) - *Hardy from exposure to fumes.*
*   **MP:** Medium (0.8x Mage base) - *Uses mana to stabilize volatile compounds.*
*   **STR:** 3
*   **END:** 5
*   **DEX:** 6 - *Precision throwing.*
*   **AGI:** 4
*   **MAG:** 7 - *Understanding of magical properties.*
*   **LCK:** 4 - *Experimental success requires luck.*

## 🎒 Starting Equipment (for GameForge)
*   **Weapon:** "Iron Pestle" (Mace type) or "Chirurgeon's Scalpel" (Dagger type)
*   **Armor:** "Apothecary's Leathers" (Light/Medium Armor)
*   **Accessory:** "Bandolier of Vials"
*   **Consumables:** 2x *Phial of Vitriol* (New Item), 1x *Bitter Panacea* (Antidote)

## ⚔️ Skill Tree: The Volatile Path (for Tactician)

### Tier 1 (Rank F)
**1. Vitriol Bomb (Active)** (Previously: Corrosive Flask)
*Description:* Hurls a flask of concentrated acid that burns the target and weakens their armor.
*Mechanics:* Deals initial damage and applies a "Corroded" debuff (-10% END/Defense) for 3 turns.
```python
"vitriol_bomb": {
    "key_id": "vitriol_bomb",
    "name": "Vitriol Bomb",
    "description": "Shatters a vial of acid, dealing damage and eroding armor.",
    "type": "Active",
    "class_id": 6,
    "mp_cost": 8,
    "power_multiplier": 1.2,
    "debuff": {"END_percent": -0.1, "duration": 3},  # Requires Tactician to implement negative buffs
    "learn_cost": 0,
    "upgrade_cost": 200,
    "scaling_stat": "DEX",  # Accuracy of the throw
    "scaling_factor": 2.4,
}
```

**2. Triage (Passive)** (Previously: Field Medic)
*Description:* Years of handling dangerous substances have made you efficient at applying remedies.
*Mechanics:* Increases the potency of healing items used on self by 20%.
```python
"triage": {
    "key_id": "triage",
    "name": "Triage",
    "description": "Increases the effectiveness of healing items.",
    "type": "Passive",
    "class_id": 6,
    "passive_bonus": {"healing_item_potency": 0.2}, # New modifier for ItemManager
    "learn_cost": 500,
    "scaling_stat": "MAG",
    "scaling_factor": 1.0,
}
```

### Tier 2 (Rank E - Proposed)
**3. Fulminating Compound (Active)** (Previously: Volatile Mixture)
*Description:* Mixes unstable reagents to create a sudden explosion.
*Mechanics:* AoE Fire damage with a chance to Stun.
```python
"fulminating_compound": {
    "key_id": "fulminating_compound",
    "name": "Fulminating Compound",
    "description": "Throw a volatile cocktail that explodes on impact.",
    "type": "Active",
    "class_id": 6,
    "mp_cost": 15,
    "power_multiplier": 1.0, # Lower multi because AoE
    "is_aoe": True,
    "status_effect": {"stun_chance": 0.2},
    "learn_cost": 1500,
    "scaling_stat": "MAG",
    "scaling_factor": 2.5,
}
```

**4. Equivalent Exchange (Passive)** (Previously: Catalyst)
*Description:* Your understanding of magical reactions amplifies your mixtures.
*Mechanics:* Increases MAG stat by 10%.
```python
"equivalent_exchange": {
    "key_id": "equivalent_exchange",
    "name": "Equivalent Exchange",
    "description": "Deep knowledge of reactions boosts magical potency.",
    "type": "Passive",
    "class_id": 6,
    "passive_bonus": {"MAG_percent": 0.1},
    "learn_cost": 1000,
    "scaling_stat": "MAG",
    "scaling_factor": 1.0,
}
```

### Ultimate (Rank B - Proposed)
**5. Mutagenic Serum** (Previously: Elixir of Transmutation)
*Description:* Drink a dangerous concoction that mutates the body for combat.
*Mechanics:* +30% STR/AGI/END for 3 turns, but takes 10% Max HP damage per turn.

## 🔗 Integration Notes

### 🛠️ For GameForge
1.  **New Item:** "Field Kit" (Accessory). Effect: +5% Potion Duration.
2.  **Class Quest:** "The Great Work".
    *   *Objective:* Collect `Primordial Ooze` (from Slimes), `Brimstone` (from Rock Elementals), and `Lunawort` (Herb).
    *   *Reward:* Unlock the *Fulminating Compound* skill or a unique "Ever-Filling Flask" (1/day potion).
3.  **Crafting Hook:** Alchemists should have a 10% chance to *not consume materials* when crafting Potions (requires update to `CraftingSystem`).

### 🧠 For Tactician
1.  **Debuff Logic:** Ensure `CombatEngine` supports negative percentage modifiers in `debuff` (e.g., `"END_percent": -0.1`).
2.  **Item Potency:** Ensure `ItemManager.use_item` checks for `healing_item_potency` passive bonus.

### 📚 For ChronicleKeeper
1.  **Achievement:** "Experimenter" - Craft 50 potions.
2.  **Title:** "Transmuter" - Unlock all Alchemist skills.
