"""
schemas.py

Defines the validation schemas for Eldoria Quest game data.
These schemas are used by DataValidator to ensure data integrity at startup.
"""

from typing import Any

# Type aliases for schema definition
SchemaType = dict[str, Any]

# --- Schema Definition Format ---
# {
#   "type": type or (type, type),
#   "required": bool (default False),
#   "min": val, "max": val,
#   "options": [val, ...],
#   "schema": { ... }, # For nested dicts
#   "keys_schema": { ... }, # For dict keys
#   "values_schema": { ... }, # For dict values
#   "element_schema": { ... }, # For lists (homogeneous)
#   "elements": [ ... ], # For lists (fixed length/structure like tuples)
# }

# --- Adventure Locations Schema ---
LOCATION_SCHEMA = {
    "name": {"type": str, "required": True},
    "emoji": {"type": str, "required": True},
    "min_rank": {
        "type": str,
        "required": True,
        "options": ["F", "E", "D", "C", "B", "A", "S", "SS", "SSS"],
    },
    "level_req": {"type": int, "required": True, "min": 1},
    "floor_depth": {"type": int, "required": True, "min": 1},
    "danger_level": {"type": int, "required": True, "min": 1},
    "duration_options": {
        "type": list,
        "required": True,
        "element_schema": {"type": int, "min": 1},
    },
    "monsters": {
        "type": list,
        "required": True,
        "element_schema": {
            "type": list,
            "length": 2,
            "elements": [{"type": str}, {"type": int}],
        },
    },
    "description": {"type": str, "required": True},
    # Optional Fields
    "night_monsters": {
        "type": list,
        "element_schema": {
            "type": list,
            "length": 2,
            "elements": [{"type": str}, {"type": int}],
        },
    },
    "gatherables": {
        "type": list,
        "element_schema": {
            "type": list,
            "length": 2,
            "elements": [{"type": str}, {"type": int}],
        },
    },
    "conditional_monsters": {
        "type": list,
        "element_schema": {
            "type": dict,
            "schema": {
                "monster_key": {"type": str, "required": True},
                "weight": {"type": int, "required": True},
                "min_level": {"type": int},
            },
        },
    },
    "special_events": {"type": list, "element_schema": {"type": str}},
    "prerequisite_location": {"type": str},
}

# --- Monsters Schema ---
MONSTER_SCHEMA = {
    "id": {"type": int, "required": True},
    "name": {"type": str, "required": True},
    "level": {"type": int, "required": True, "min": 1},
    "tier": {
        "type": str,
        "required": True,
        "options": ["Normal", "Elite", "Boss", "Raid"],
    },
    "hp": {"type": int, "required": True, "min": 1},
    "atk": {"type": int, "required": True, "min": 0},
    "def": {"type": int, "required": True, "min": 0},
    "xp": {"type": int, "required": True, "min": 0},
    "drops": {
        "type": list,
        "element_schema": {
            "type": list,
            "length": 2,
            "elements": [{"type": str}, {"type": int, "min": 0, "max": 100}],
        },
    },
    "skills": {"type": list, "element_schema": {"type": str}},
    "description": {"type": str, "required": True},
}

# --- Consumables Schema ---
CONSUMABLE_SCHEMA = {
    "id": {"type": str, "required": True},
    "name": {"type": str, "required": True},
    "type": {"type": str, "required": True},
    "effect": {
        "type": dict,
        "required": True,
        # keys/values can vary, usually str: int
        "keys_schema": {"type": str},
        "values_schema": {"type": (int, float, str, bool)},
    },
    "rarity": {"type": str, "required": True},
    "description": {"type": str, "required": True},
}

# --- Equipment Schema ---
EQUIPMENT_SCHEMA = {
    "name": {"type": str, "required": True},
    "slot": {"type": str, "required": True},
    "rarity": {
        "type": str,
        "required": True,
        "options": ["Common", "Uncommon", "Rare", "Epic", "Legendary", "Mythical"],
    },
    "level_req": {"type": int, "required": True, "min": 1},
    "stats_bonus": {
        "type": dict,
        "required": True,
        "keys_schema": {"type": str},
        "values_schema": {"type": int},
    },
    "description": {"type": str, "required": True},
    # Optional
    "class_restrictions": {"type": list, "element_schema": {"type": str}},
    "rank_restriction": {"type": str},
}

# --- Materials Schema ---
MATERIAL_SCHEMA = {
    "name": {"type": str, "required": True},
    "description": {"type": str, "required": True},
    "rarity": {
        "type": str,
        "required": True,
        "options": ["Common", "Uncommon", "Rare", "Epic", "Legendary", "Mythical"],
    },
    "value": {"type": int, "required": True, "min": 0},
}

# --- Quest Items Schema ---
QUEST_ITEM_SCHEMA = {
    "id": {"type": str, "required": True},
    "name": {"type": str, "required": True},
    "rarity": {
        "type": str,
        "required": True,
        "options": ["Common", "Uncommon", "Rare", "Epic", "Legendary", "Mythical"],
    },
    "notes": {"type": str, "required": True},
}


# --- Faction Schema ---
FACTION_SCHEMA = {
    "name": {"type": str, "required": True},
    "emoji": {"type": str, "required": True},
    "description": {"type": str, "required": True},
    "ranks": {
        "type": dict,
        "required": True,
        "keys_schema": {"type": str},
        "values_schema": {
            "type": dict,
            "schema": {
                "title": {"type": str, "required": True},
                "reputation_needed": {"type": int, "required": True, "min": 0},
                "reward": {"type": (dict, type(None)), "required": True},
            },
        },
    },
    "interests": {
        "type": dict,
        "required": True,
        "keys_schema": {"type": str},
        "values_schema": {"type": (int, float, list)},
    },
    "favored_locations": {
        "type": list,
        "required": True,
        "element_schema": {"type": str},
    },
}


# --- Codex Schema ---
CODEX_SCHEMA = {
    "monsters": {
        "type": dict,
        "keys_schema": {"type": str},
        "values_schema": {
            "type": dict,
            "schema": {
                "lore_extended": {"type": str, "required": True},
                "unlock_thresholds": {
                    "type": dict,
                    "required": True,
                    "schema": {
                        "basic": {"type": int, "required": True},
                        "stats": {"type": int, "required": True},
                        "lore": {"type": int, "required": True},
                    },
                },
            },
        },
    },
    "items": {
        "type": dict,
        "keys_schema": {"type": str},
        "values_schema": {
            "type": dict,
            "schema": {"lore_extended": {"type": str, "required": True}},
        },
    },
    "locations": {
        "type": dict,
        "keys_schema": {"type": str},
        "values_schema": {
            "type": dict,
            "schema": {"lore_extended": {"type": str, "required": True}},
        },
    },
    "factions": {
        "type": dict,
        "keys_schema": {"type": str},
        "values_schema": {
            "type": dict,
            "schema": {"lore_extended": {"type": str, "required": True}},
        },
    },
}
