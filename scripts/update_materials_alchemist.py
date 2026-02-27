import json
import os

filepath = "game_systems/data/materials.json"

new_materials = {
    "primordial_ooze": {
        "name": "Primordial Ooze",
        "description": "A shifting, viscous substance found in ancient slimes.",
        "rarity": "Uncommon",
        "value": 25
    },
    "brimstone": {
        "name": "Brimstone",
        "description": "Yellowish rock that smells of rotten eggs and fire.",
        "rarity": "Uncommon",
        "value": 30
    },
    "lunawort": {
        "name": "Lunawort",
        "description": "A pale herb that glows faintly under moonlight.",
        "rarity": "Uncommon",
        "value": 45
    }
}

try:
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Update only if missing to prevent overwrite of manual changes
    updated = False
    for k, v in new_materials.items():
        if k not in data:
            data[k] = v
            print(f"Added {k}")
            updated = True
        else:
            print(f"Skipped {k} (already exists)")

    if updated:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print("Materials updated successfully.")
    else:
        print("No updates needed.")

except Exception as e:
    print(f"Error updating materials: {e}")
