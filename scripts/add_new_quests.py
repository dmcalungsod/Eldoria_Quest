"""
scripts/add_new_quests.py

Safely appends new quest definitions to game_systems/data/quests.json.
Validates that IDs do not conflict.
"""

import json
import os
import sys

# New Quests to Add
NEW_QUESTS = [
    {
        "id": 74,
        "title": "The Stone-Skin Symptoms",
        "tier": "D",
        "quest_giver": "Alchemist Vane",
        "location": "Deepgrove Roots",
        "summary": "Collect samples from petrified wildlife.",
        "description": "Refugees from the outer districts are turning to stone. Alchemist Vane of the Grey Ward needs tissue samples from infected beasts in the Deepgrove to study the pathogen before it breaches the quarantine.",
        "objectives": {
            "collect": {"Petrified Heart": 3},
            "examine": {"Calcified Corpse": 1}
        },
        "flavor_text": {
            "collect:Petrified Heart": "The heart is heavy and cold, turned completely to grey stone.",
            "examine:Calcified Corpse": "The victim's face is frozen in a silent scream. Moss is already growing in the cracks."
        },
        "rewards": {
            "exp": 600,
            "aurum": 150,
            "item": "Grey Ward Mask"
        }
    },
    {
        "id": 75,
        "title": "The Basilisk's Bile",
        "tier": "D",
        "quest_giver": "Alchemist Vane",
        "location": "The Ashlands",
        "summary": "Hunt a Basilisk for its bile.",
        "description": "The Stone-Skin Plague is magical in nature. Vane believes the acidic bile of an Ash Basilisk can dissolve the petrification curse. These beasts prowl the borders of the Ashlands.",
        "prerequisites": [74],
        "objectives": {
            "defeat": {"Ember Salamander": 1},
            "collect": {"Basilisk Bile": 1}
        },
        "flavor_text": {
            "defeat:Ember Salamander": "The beast hisses one last time before dissolving into ash.",
            "collect:Basilisk Bile": "The bile smokes in the vial, smelling of acid and old earth."
        },
        "rewards": {
            "exp": 800,
            "aurum": 200,
            "item": "Unstable Antidote"
        }
    },
    {
        "id": 76,
        "title": "The Cure: For the Few",
        "tier": "D",
        "quest_giver": "Merchant Gilded-Tongue",
        "location": "Guild Hall",
        "summary": "Sell the antidote to a noble house. (Choice A)",
        "description": "A merchant intercepts you. 'Why waste such a miracle on the dregs? House Valerius will pay a fortune for that antidote. They can replicate it... eventually. Secure your future, adventurer.'",
        "prerequisites": [75],
        "exclusive_group": "stone_skin_choice",
        "objectives": {
            "deliver": {"Unstable Antidote": 1}
        },
        "flavor_text": {
            "deliver:Unstable Antidote": "The courier accepts the vial with a sneer. 'Wise choice. The coin is yours.'"
        },
        "rewards": {
            "exp": 400,
            "aurum": 1500,
            "title": "Mercenary"
        }
    },
    {
        "id": 77,
        "title": "The Cure: For the Many",
        "tier": "D",
        "quest_giver": "Alchemist Vane",
        "location": "Grey Ward Outpost",
        "summary": "Deliver the antidote to the Grey Ward. (Choice B)",
        "description": "Alchemist Vane is waiting. 'It's not enough for everyone yet, but with this sample, we can save the quarantine zone. We can stop the spread. The city owes you a debt.'",
        "prerequisites": [75],
        "exclusive_group": "stone_skin_choice",
        "objectives": {
            "deliver": {"Unstable Antidote": 1}
        },
        "flavor_text": {
            "deliver:Unstable Antidote": "Vane's hands shake as he takes the vial. 'You did good. Real good.'"
        },
        "rewards": {
            "exp": 1000,
            "aurum": 500,
            "item": "Alchemist's Retort"
        }
    }
]

def main():
    json_path = os.path.join("game_systems", "data", "quests.json")

    if not os.path.exists(json_path):
        print(f"Error: {json_path} not found.")
        sys.exit(1)

    try:
        with open(json_path, encoding="utf-8") as f:
            quests = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        sys.exit(1)

    existing_ids = {q["id"] for q in quests}

    print(f"Loaded {len(quests)} quests. Max ID: {max(existing_ids) if existing_ids else 0}")

    added_count = 0
    for new_q in NEW_QUESTS:
        if new_q["id"] in existing_ids:
            print(f"Skipping Quest {new_q['id']} ({new_q['title']}) - ID already exists.")
            continue

        quests.append(new_q)
        added_count += 1
        print(f"Added Quest {new_q['id']}: {new_q['title']}")

    if added_count > 0:
        # Sort by ID for cleanliness
        quests.sort(key=lambda x: x["id"])

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(quests, f, indent=2, ensure_ascii=False)
        print(f"Successfully saved {len(quests)} quests to {json_path}.")
    else:
        print("No new quests were added.")

if __name__ == "__main__":
    main()
