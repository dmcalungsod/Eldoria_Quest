import json

filepath = "game_systems/data/quests.json"

new_quest = {
    "id": 900,
    "title": "The Great Work",
    "tier": "E",
    "quest_giver": "Kaelen, the First Alchemist",
    "location": "Grey Ward District",
    "summary": "Collect rare reagents to prove your mastery of alchemy.",
    "description": "To truly understand the nature of the Veil, one must deconstruct it. Bring me Primordial Ooze, Brimstone, and Lunawort. Only then can you begin the Great Work.",
    "objectives": {
        "collect": {
            "primordial_ooze": 3,
            "brimstone": 3,
            "lunawort": 3
        }
    },
    "rewards": {
        "exp": 500,
        "aurum": 300
    }
}

try:
    with open(filepath, encoding="utf-8") as f:
        data = json.load(f)

    # Check if quest exists by title to avoid duplicates
    exists = False
    for q in data:
        if q["title"] == new_quest["title"]:
            exists = True
            break

    if not exists:
        # Find max ID to auto-increment safely
        max_id = max([q["id"] for q in data])
        new_quest["id"] = max_id + 1
        data.append(new_quest)

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"Added quest '{new_quest['title']}' with ID {new_quest['id']}.")
    else:
        print("Quest already exists.")

except Exception as e:
    print(f"Error updating quests: {e}")
