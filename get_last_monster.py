import json

def get_last_monster():
    with open('game_systems/data/monsters.json', 'r') as f:
        data = json.load(f)
        last_key = list(data.keys())[-1]
        print(f"Last key: {last_key}")
        print(json.dumps(data[last_key], indent=4))

get_last_monster()
