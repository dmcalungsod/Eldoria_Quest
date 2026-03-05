import json

def update_monsters():
    with open('game_systems/data/monsters.json', 'r', encoding='utf-8') as f:
        monsters = json.load(f)

    # Frost Gargoyle
    monsters["frost_gargoyle"] = {
        "id": 172,
        "name": "Frost Gargoyle",
        "level": 32,
        "tier": "Elite",
        "hp": 3200,
        "atk": 180,
        "def": 210,
        "xp": 1200,
        "drops": [
            ["raw_star_metal_block", 30],
            ["refined_stone", 50],
            ["magic_stone_polished", 20]
        ],
        "skills": ["crushing_slam", "ice_spear"],
        "description": "A stone guardian brought to life by the biting cold of the Howling Peaks."
    }

    # Storm Drake
    monsters["storm_drake"] = {
        "id": 173,
        "name": "Storm Drake",
        "level": 35,
        "tier": "Boss",
        "hp": 8500,
        "atk": 250,
        "def": 180,
        "xp": 3500,
        "drops": [
            ["vial_of_drake_blood", 100],
            ["dragon_scale", 40],
            ["magic_stone_flawless", 30]
        ],
        "skills": ["thunder_call", "dragon_breath", "whirlwind"],
        "description": "A massive beast of the Howling Peaks, its scales crackling with lightning."
    }

    with open('game_systems/data/monsters.json', 'w', encoding='utf-8') as f:
        json.dump(monsters, f, indent=4, ensure_ascii=False)


def update_locations():
    with open('game_systems/data/adventure_locations.json', 'r', encoding='utf-8') as f:
        locations = json.load(f)

    locations["howling_peaks"] = {
        "name": "The Howling Peaks",
        "emoji": "🏔️",
        "min_rank": "A",
        "level_req": 30,
        "duration_options": [60, 120, 240, 480],
        "monsters": [
            ["frost_gargoyle", 60],
            ["storm_drake", 10],
            ["monster_111", 30]  # Frost Wolf
        ],
        "bosses": ["storm_drake"],
        "materials": ["raw_star_metal_block", "dragon_scale", "refined_stone"],
        "quest_items": ["vial_of_drake_blood"],
        "floor_depth": 50,
        "danger_level": 8
    }

    with open('game_systems/data/adventure_locations.json', 'w', encoding='utf-8') as f:
        json.dump(locations, f, indent=4, ensure_ascii=False)


update_monsters()
update_locations()
