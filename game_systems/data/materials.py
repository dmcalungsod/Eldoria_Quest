"""
materials.py

Defines all 'Material' type items found in Eldoria.
REBALANCED: Sell values increased to improve economy flow.
"""

MATERIALS = {
    # --- Magic Stones (Core Income) ---
    "magic_stone_fragment": {
        "name": "Magic Stone Fragment",
        "description": "A tiny, impure shard of crystallized mana.",
        "rarity": "Common",
        "value": 8,  # Up from 5
    },
    "magic_stone_small": {
        "name": "Magic Stone (Small)",
        "description": "A small, cloudy stone of mana harvested from a low-level monster.",
        "rarity": "Common",
        "value": 15,  # Up from 8
    },
    "magic_stone_medium": {
        "name": "Magic Stone (Medium)",
        "description": "A decent-sized stone pulsating with the energy of the Veil.",
        "rarity": "Uncommon",
        "value": 50,  # Up from 30
    },
    "magic_stone_large": {
        "name": "Magic Stone (Large)",
        "description": "A heavy, fist-sized stone that hums with the raw power of the Sundering.",
        "rarity": "Rare",
        "value": 180,  # Up from 120
    },
    "magic_stone_flawless": {
        "name": "Magic Stone (Flawless)",
        "description": "A brilliant, pure crystal of condensed mana. The lifeblood of Astraeon.",
        "rarity": "Epic",
        "value": 750,  # Up from 500
    },
    # --- Event Materials ---
    "ectoplasm": {
        "name": "Ectoplasm",
        "description": "A glowing, viscous substance left by spectral entities.",
        "rarity": "Uncommon",
        "value": 50,
    },
    "blood_shard": {
        "name": "Blood Shard",
        "description": "A jagged crystal pulsing with a crimson light. It feels warm to the touch.",
        "rarity": "Rare",
        "value": 200,
    },
    "elemental_mote": {
        "name": "Elemental Mote",
        "description": "A flickering spark of raw elemental energy, unstable and valuable.",
        "rarity": "Uncommon",
        "value": 40,
    },
    # --- Forest Zone Drops ---
    "goblin_ear": {
        "name": "Goblin Ear",
        "description": "Proof of defeating a goblin.",
        "rarity": "Common",
        "value": 10,  # Up from 5
    },
    "wolf_fang": {
        "name": "Wolf Fang",
        "description": "A sharp, unbroken fang from a forest wolf.",
        "rarity": "Common",
        "value": 18,  # Up from 10
    },
    "slime_gel": {
        "name": "Slime Gel",
        "description": "Sticky, caustic residue from a slime.",
        "rarity": "Common",
        "value": 8,  # Up from 3
    },
    "spider_silk": {
        "name": "Spider Silk",
        "description": "Strong, lightweight thread from a forest spider.",
        "rarity": "Uncommon",
        "value": 25,  # Up from 15
    },
    "treant_branch": {
        "name": "Treant Branch",
        "description": "A branch from a Treant, still thrumming with faint life magic.",
        "rarity": "Uncommon",
        "value": 35,  # Up from 20
    },
    "boar_tusk": {
        "name": "Corrupted Tusk",
        "description": "A tusk from a Ravaged Boar.",
        "rarity": "Uncommon",
        "value": 40,  # Up from 22
    },
    "boar_meat": {
        "name": "Raw Boar Meat",
        "description": "A slab of meat from a wild boar.",
        "rarity": "Common",
        "value": 15,
    },
    "boss_talon": {
        "name": "Forest Boss Talon",
        "description": "A massive talon from a guardian of the forest.",
        "rarity": "Rare",
        "value": 400,  # Up from 250
    },
    # --- Wild Gatherable Materials ---
    "medicinal_herb": {
        "name": "Medicinal Herb",
        "description": "A common herb with slight healing properties.",
        "rarity": "Common",
        "value": 5,
    },
    "iron_ore": {
        "name": "Iron Ore",
        "description": "A chunk of raw iron suitable for smelting.",
        "rarity": "Common",
        "value": 12,
    },
    "luminescent_crystal": {
        "name": "Luminescent Crystal",
        "description": "A crystal that glows with a cold inner light.",
        "rarity": "Uncommon",
        "value": 45,
    },
    "ancient_wood": {
        "name": "Ancient Wood",
        "description": "A dense piece of wood from an old tree.",
        "rarity": "Uncommon",
        "value": 25,
    },
    # --- The Sunken Grotto Materials (Rank C) ---
    "coral_fragment": {
        "name": "Coral Fragment",
        "description": "A piece of colorful, hardened coral.",
        "rarity": "Common",
        "value": 12,
    },
    "bioluminescent_scale": {
        "name": "Bioluminescent Scale",
        "description": "A fish scale that glows faintly in the dark.",
        "rarity": "Uncommon",
        "value": 30,
    },
    "pearl": {
        "name": "Pearl",
        "description": "A lustrous sphere formed inside a giant clam.",
        "rarity": "Rare",
        "value": 120,
    },
    "siren_voice_box": {
        "name": "Siren Voice Box",
        "description": "An organ that can mimic any sound.",
        "rarity": "Rare",
        "value": 150,
    },
    "abyssal_pearl": {
        "name": "Abyssal Pearl",
        "description": "A pearl as black as the depths, radiating cold energy.",
        "rarity": "Epic",
        "value": 800,
    },
    # --- RARE CRAFTING MATERIALS ---
    "shadow_essence": {
        "name": "Shadow Essence",
        "description": "A vial of swirling darkness gathered from spirits.",
        "rarity": "Rare",
        "value": 150,
    },
    "mithril_ore": {
        "name": "Mithril Ore",
        "description": "Lightweight, silvery ore prized by smiths.",
        "rarity": "Rare",
        "value": 120,
    },
    "ironwood_heart": {
        "name": "Ironwood Heart",
        "description": "The petrified heart of an Elder Treant.",
        "rarity": "Rare",
        "value": 200,
    },
    # --- EPIC CRAFTING MATERIALS ---
    "crystal_heart": {
        "name": "Crystal Heart",
        "description": "The pulsating core of a crystalline construct.",
        "rarity": "Epic",
        "value": 900,
    },
    "titan_shard": {
        "name": "Titan Shard",
        "description": "A fragment of metal so hard it feels impossible.",
        "rarity": "Epic",
        "value": 800,
    },
    "celestial_dust": {
        "name": "Celestial Dust",
        "description": "Glimmering dust that falls from the cracks in the sky, cold as the Void.",
        "rarity": "Epic",
        "value": 1000,
    },
    # --- Clockwork Halls Materials (Rank B) ---
    "brass_gear": {
        "name": "Brass Gear",
        "description": "A precisely machined gear that still spins on its own.",
        "rarity": "Common",
        "value": 15,
    },
    "copper_wire": {
        "name": "Copper Wire",
        "description": "A coil of conductive wire.",
        "rarity": "Common",
        "value": 18,
    },
    "spring_coil": {
        "name": "Spring Coil",
        "description": "A tense spring ready to snap.",
        "rarity": "Common",
        "value": 12,
    },
    "steam_core": {
        "name": "Steam Core",
        "description": "A canister of pressurized steam and mana.",
        "rarity": "Rare",
        "value": 150,
    },
    "clockwork_heart": {
        "name": "Clockwork Heart",
        "description": "The complex engine of a master automaton.",
        "rarity": "Epic",
        "value": 850,
    },
    # --- Molten Caldera Materials ---
    "obsidian_shard": {
        "name": "Obsidian Shard",
        "description": "A razor-sharp shard of volcanic glass.",
        "rarity": "Common",
        "value": 20,
    },
    "fire_essence": {
        "name": "Fire Essence",
        "description": "A flickering mote of elemental fire.",
        "rarity": "Uncommon",
        "value": 55,
    },
    "magma_core": {
        "name": "Magma Core",
        "description": "The cooling heart of a magma construct.",
        "rarity": "Rare",
        "value": 200,
    },
    "dragon_scale": {
        "name": "Dragon Scale",
        "description": "A scale from a Lava Drake, hot to the touch.",
        "rarity": "Epic",
        "value": 1100,
    },
    # --- Frostfall Expanse Materials ---
    "frost_crystal": {
        "name": "Frost Crystal",
        "description": "A shard of ice that never melts.",
        "rarity": "Uncommon",
        "value": 45,
    },
    "winter_wolf_pelt": {
        "name": "Winter Wolf Pelt",
        "description": "Thick white fur, warm enough to survive the tundra.",
        "rarity": "Common",
        "value": 25,
    },
    "ice_core": {
        "name": "Ice Core",
        "description": "The frozen heart of an ice construct.",
        "rarity": "Rare",
        "value": 180,
    },
    "frozen_scale": {
        "name": "Frozen Scale",
        "description": "A scale radiating intense cold.",
        "rarity": "Epic",
        "value": 950,
    },
    # --- The Void Sanctum Materials (Rank S) ---
    "void_dust": {
        "name": "Void Dust",
        "description": "A pile of fine, dark dust that drinks the light around it.",
        "rarity": "Common",
        "value": 30,
    },
    "abyssal_shackle": {
        "name": "Abyssal Shackle",
        "description": "A broken chain link made of an unknown, cold metal.",
        "rarity": "Common",
        "value": 35,
    },
    "entropy_crystal": {
        "name": "Entropy Crystal",
        "description": "A crystal that constantly shifts its shape.",
        "rarity": "Uncommon",
        "value": 60,
    },
    "null_stone": {
        "name": "Null Stone",
        "description": "A heavy stone that feels like it weighs nothing. A paradox of the Void.",
        "rarity": "Rare",
        "value": 250,
    },
    "void_heart": {
        "name": "Void Heart",
        "description": "A pulsating core of pure nothingness. It hungers for the light.",
        "rarity": "Epic",
        "value": 1500,
    },
    # --- The Ashlands Materials (Rank D) ---
    "ash_blossom": {
        "name": "Ash Blossom",
        "description": "A pale, hardy flower that grows in volcanic soil.",
        "rarity": "Common",
        "value": 15,
    },
    "scorched_chitin": {
        "name": "Scorched Chitin",
        "description": "A piece of insect shell, hardened by heat.",
        "rarity": "Uncommon",
        "value": 35,
    },
    # --- Refined Materials ---
    "iron_ingot": {
        "name": "Iron Ingot",
        "description": "A solid bar of refined iron, ready for the forge.",
        "rarity": "Common",
        "value": 40,
    },
    "steel_ingot": {
        "name": "Steel Ingot",
        "description": "An alloy of iron and carbon, harder and more durable.",
        "rarity": "Uncommon",
        "value": 70,
    },
    "refined_magic_stone": {
        "name": "Refined Magic Stone",
        "description": "A pure, cut stone that hums with stable mana.",
        "rarity": "Uncommon",
        "value": 45,
    },
    "cured_leather": {
        "name": "Cured Leather",
        "description": "Tough, treated leather suitable for armor.",
        "rarity": "Common",
        "value": 30,
    },
    "hardwood_plank": {
        "name": "Hardwood Plank",
        "description": "A smooth, sturdy plank of ancient wood.",
        "rarity": "Uncommon",
        "value": 80,
    },
    # --- Alchemical Byproducts ---
    "slag": {
        "name": "Alchemical Slag",
        "description": "A useless lump of burnt material from a failed experiment.",
        "rarity": "Common",
        "value": 1,
    },
}
