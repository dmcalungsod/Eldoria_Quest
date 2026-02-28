import json


def analyze():
    print("Running combat metrics simulation...")
    with open("game_systems/data/monsters.json") as f:
        monsters = json.load(f)

    for k, v in monsters.items():
        if v.get("tier") == "Boss" and v.get("level", 0) > 30:
            print(f"Boss: {v['name']} (Lvl {v['level']}) - Drops: {v.get('drops', [])}")


if __name__ == "__main__":
    analyze()
