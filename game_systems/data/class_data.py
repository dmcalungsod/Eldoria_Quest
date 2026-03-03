"""
class_data.py

Contains all class definitions for Eldoria Quest.
Class descriptions are written in a high-fantasy, novel-like tone to match the world of
'Eldoria: The Shattered Veil'.

Stats: STR, END, DEX, AGI, MAG, LCK
"""

CLASSES = {
    "Warrior": {
        "id": 1,
        "description": (
            "Forged in the roar of battle and tempered by hardship, the Warrior stands as the "
            "unyielding bulwark of any fellowship. Clad in steel and armed with unwavering resolve, "
            "they wade into the fray where others falter. Their might shatters shields, their "
            "presence alone turning the tide as they hold the line against horrors that would "
            "break lesser souls."
        ),
        "stats": {"STR": 8, "END": 7, "DEX": 5, "AGI": 3, "MAG": 1, "LCK": 1},
        "allowed_slots": [
            "sword",
            "greatsword",
            "mace",
            "shield",  # Weapons
            "helm",
            "heavy_armor",
            "heavy_gloves",
            "heavy_boots",
            "heavy_legs",  # Armor
            "belt",
            "accessory",  # Misc
        ],
    },
    "Alchemist": {
        "id": 6,
        "description": (
            "A pragmatic survivor who views the Sundering not as a curse, but a chemical reaction "
            "to be understood. While Mages channel the Veil and Clerics pray to it, Alchemists "
            "bottle it. They use volatile mixtures to control the battlefield, stripping enemy "
            "defenses and turning the environment against them."
        ),
        "stats": {"STR": 3, "END": 5, "DEX": 6, "AGI": 4, "MAG": 7, "LCK": 4},
        "allowed_slots": [
            "mace",
            "dagger",
            "tome",  # Weapons
            "alchemist_coat",  # Class-specific
            "medium_armor",
            "medium_gloves",
            "medium_boots",
            "medium_legs",
            "leather_cap",  # Medium Armor
            "robe",
            "hood",
            "gloves",
            "boots",
            "legs",  # Light Armor
            "belt",
            "accessory",  # Misc
        ],
    },
    "Mage": {
        "id": 2,
        "description": (
            "Students of the unseen, Mages bend the arcane currents that swirl beneath Eldoria’s "
            "fractured Veil. Their flesh is fragile, but their will commands storms of fire, ice, "
            "and eldritch brilliance. A single misstep can spell doom—yet a single spell can "
            "reshape the battlefield, or unmake an enemy in a heartbeat."
        ),
        "stats": {"STR": 2, "END": 3, "DEX": 4, "AGI": 5, "MAG": 9, "LCK": 2},
        "allowed_slots": [
            "staff",
            "wand",
            "tome",
            "orb",  # Weapons
            "hood",
            "robe",
            "gloves",
            "boots",
            "legs",  # Armor
            "belt",
            "accessory",  # Misc
        ],
    },
    "Rogue": {
        "id": 3,
        "description": (
            "Half-whisper, half-shadow, the Rogue is the embodiment of lethal subtlety. They slip "
            "through cracks in both walls and armor, striking with precision where foes are blind. "
            "Quick of hand and quicker of wit, they thrive on misdirection—turning every mistake "
            "their enemies make into a fatal opening."
        ),
        "stats": {"STR": 4, "END": 4, "DEX": 7, "AGI": 8, "MAG": 1, "LCK": 3},
        "allowed_slots": [
            "dagger",
            "offhand_dagger",
            "bow",  # Weapons
            "leather_hood",
            "rogue_armor",
            "medium_gloves",
            "medium_boots",
            "medium_legs",  # Armor
            "belt",
            "accessory",  # Misc
        ],
    },
    "Cleric": {
        "id": 4,
        "description": (
            "Chosen by divine whispers that echo beyond the Veil, Clerics walk as both healers and "
            "harbingers. They mend shattered flesh with sacred light, yet wield holy wrath against "
            "the profane. To their allies they are salvation—to their enemies, the radiant judgment "
            "they never see coming."
        ),
        # --- BUFFED STATS ---
        "stats": {"STR": 5, "END": 7, "DEX": 3, "AGI": 3, "MAG": 8, "LCK": 1},
        "allowed_slots": [
            "mace",
            "shield",
            "staff",
            "tome",  # Weapons
            "miter",
            "vestments",
            "gloves",
            "boots",
            "legs",  # Armor
            "belt",
            "accessory",  # Misc
        ],
    },
    "Ranger": {
        "id": 5,
        "description": (
            "Children of wind and wood, Rangers tread paths where others see only wilderness. Their "
            "arrows whistle with uncanny accuracy, guided by instinct honed under open skies. Whether "
            "tracking beasts twisted by the Sundering or scouting the edges of darkness, they strike "
            "with the wild’s silent fury and vanish just as swiftly."
        ),
        "stats": {"STR": 4, "END": 5, "DEX": 8, "AGI": 6, "MAG": 2, "LCK": 2},
        "allowed_slots": [
            "bow",
            "dagger",
            "quiver",  # Weapons
            "leather_cap",
            "medium_armor",
            "medium_gloves",
            "medium_boots",
            "medium_legs",  # Armor
            "belt",
            "accessory",  # Misc
        ],
    },
}
