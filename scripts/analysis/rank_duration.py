import json


def analyze():
    with open("game_systems/data/adventure_locations.json") as f:
        locations = json.load(f)

    for k, v in locations.items():
        print(f"{v['name']} (Rank {v.get('rank', 'N/A')}, Level {v.get('level_req', 'N/A')})")


if __name__ == "__main__":
    analyze()
