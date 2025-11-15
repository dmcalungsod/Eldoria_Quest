"""
CLASS_EQUIPMENTS — Eldoria Quest (Class-specific beginner sets)
--------------------------------------------------------------
Stats: STR, END, DEX, AGI, MAG, LCK
"""

from math import floor

CLASSES = ["Warrior", "Mage", "Rogue", "Cleric", "Ranger"]
SLOTS = {
    "Warrior": [
        "weapon",
        "chest",
        "hands",
        "legs",
        "feet",
        "accessory",
        "weapon2",
        "shield",
        "helm",
        "belt",
    ],
    "Mage": [
        "weapon",
        "chest",
        "hands",
        "legs",
        "feet",
        "accessory",
        "tome",
        "orb",
        "robe",
        "hood",
    ],
    "Rogue": [
        "weapon",
        "chest",
        "hands",
        "legs",
        "feet",
        "accessory",
        "hood",
        "dagger",
        "boots",
        "cloak",
    ],
    "Cleric": [
        "weapon",
        "chest",
        "hands",
        "legs",
        "feet",
        "accessory",
        "miter",
        "chalice",
        "vest",
        "bracer",
    ],
    "Ranger": [
        "weapon",
        "chest",
        "hands",
        "legs",
        "feet",
        "accessory",
        "quiver",
        "cloak",
        "cap",
        "strap",
    ],
}

CLASS_EQUIPMENTS = {}
CLASS_SETS = {}
eid = 1

for cls in CLASSES:
    set_name = f"Beginner's {cls} Ward"
    CLASS_SETS[set_name] = {
        "pieces": [],
        "set_bonus": (
            {"STR": 2, "END": 3}
            if cls == "Warrior"
            else (
                {"MAG": 3, "AGI": 2}
                if cls == "Mage"
                else (
                    {"DEX": 3, "AGI": 2, "LCK": 1}
                    if cls == "Rogue"
                    else (
                        {"MAG": 3, "END": 2}
                        if cls == "Cleric"
                        else {"DEX": 3, "END": 1, "AGI": 1}
                    )
                )
            )
        ),  # Ranger
    }

    # Create 5 set pieces (level req 1-12)
    for i in range(5):
        slot = SLOTS[cls][i]
        level_req = 1 + i * 2
        # stat flavor per class
        if cls == "Warrior":
            stats = {"STR": 2 + i, "END": 1 + i}
        elif cls == "Mage":
            stats = {"MAG": 3 + i, "AGI": 1 + (i // 2)}
        elif cls == "Rogue":
            stats = {"DEX": 3 + i, "AGI": 1 + i}
        elif cls == "Cleric":
            stats = {"MAG": 3 + i, "END": 1 + (i // 2)}
        else:  # Ranger
            stats = {"DEX": 2 + i, "AGI": 1 + i}

        key = f"{cls.lower()}_set_{i+1}"
        CLASS_EQUIPMENTS[key] = {
            "id": eid,
            "class": cls,
            "name": f"{set_name} — {slot.title()}",
            "slot": slot,
            "rarity": "Uncommon",
            "level_req": level_req,
            "stats_bonus": stats,
            "set": set_name,
            "description": f"A piece of the {set_name}. Worn by fledgling {cls.lower()}s of the glade.",
        }
        CLASS_SETS[set_name]["pieces"].append(key)
        eid += 1

    # Create 5 additional class-specific items (make up to 10 per class)
    for j in range(5):
        slot = SLOTS[cls][5 + j]
        level_req = min(30, 2 + j * 3)
        # slightly stronger rarities as j increases
        rarity = "Common" if j < 2 else "Uncommon" if j < 4 else "Rare"
        if cls == "Warrior":
            stats = {"STR": 3 + j * 1, "END": 2 + j}
        elif cls == "Mage":
            stats = {"MAG": 4 + j * 1, "AGI": 2 + j}
        elif cls == "Rogue":
            stats = {"DEX": 4 + j, "AGI": 1 + j, "LCK": 1}
        elif cls == "Cleric":
            stats = {"MAG": 4 + j, "END": 1 + j}
        else:
            stats = {"DEX": 3 + j, "AGI": 2 + j}

        key = f"{cls.lower()}_extra_{j+1}"
        CLASS_EQUIPMENTS[key] = {
            "id": eid,
            "class": cls,
            "name": f"{cls} {slot.title()} of the Glade",
            "slot": slot,
            "rarity": rarity,
            "level_req": level_req,
            "stats_bonus": stats,
            "set": None,
            "description": f"A {rarity.lower()} {slot} favored by {cls.lower()} apprentices.",
        }
        eid += 1

# export
__all__ = ["CLASS_EQUIPMENTS", "CLASS_SETS"]
