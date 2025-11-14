"""
class_data.py

Contains all class definitions for Eldoria Quest.
Class descriptions are written in a high-fantasy, novel-like tone to match the world of
'Eldoria: The Shattered Veil'.
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
        "stats": {
            "STR": 8, "DEX": 4, "CON": 7, "INT": 2, "WIS": 3, "CHA": 4, "LCK": 2
        }
    },

    "Mage": {
        "id": 2,
        "description": (
            "Students of the unseen, Mages bend the arcane currents that swirl beneath Eldoria’s "
            "fractured Veil. Their flesh is fragile, but their will commands storms of fire, ice, "
            "and eldritch brilliance. A single misstep can spell doom—yet a single spell can "
            "reshape the battlefield, or unmake an enemy in a heartbeat."
        ),
        "stats": {
            "STR": 2, "DEX": 3, "CON": 3, "INT": 9, "WIS": 7, "CHA": 4, "LCK": 2
        }
    },

    "Rogue": {
        "id": 3,
        "description": (
            "Half-whisper, half-shadow, the Rogue is the embodiment of lethal subtlety. They slip "
            "through cracks in both walls and armor, striking with precision where foes are blind. "
            "Quick of hand and quicker of wit, they thrive on misdirection—turning every mistake "
            "their enemies make into a fatal opening."
        ),
        "stats": {
            "STR": 4, "DEX": 9, "CON": 4, "INT": 3, "WIS": 2, "CHA": 6, "LCK": 2
        }
    },

    "Cleric": {
        "id": 4,
        "description": (
            "Chosen by divine whispers that echo beyond the Veil, Clerics walk as both healers and "
            "harbingers. They mend shattered flesh with sacred light, yet wield holy wrath against "
            "the profane. To their allies they are salvation—to their enemies, the radiant judgment "
            "they never see coming."
        ),
        "stats": {
            "STR": 5, "DEX": 2, "CON": 6, "INT": 4, "WIS": 9, "CHA": 5, "LCK": 1
        }
    },

    "Ranger": {
        "id": 5,
        "description": (
            "Children of wind and wood, Rangers tread paths where others see only wilderness. Their "
            "arrows whistle with uncanny accuracy, guided by instinct honed under open skies. Whether "
            "tracking beasts twisted by the Sundering or scouting the edges of darkness, they strike "
            "with the wild’s silent fury and vanish just as swiftly."
        ),
        "stats": {
            "STR": 4, "DEX": 8, "CON": 5, "INT": 3, "WIS": 6, "CHA": 3, "LCK": 1
        }
    }
}
