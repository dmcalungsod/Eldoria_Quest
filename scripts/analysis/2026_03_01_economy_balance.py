import json
import os
import sys

# Ensure script works from any directory by finding the project root
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

def load_json(filepath):
    full_path = os.path.join(PROJECT_ROOT, filepath)
    if not os.path.exists(full_path):
        print(f"File not found: {full_path}")
        sys.exit(1)
    with open(full_path, 'r') as f:
        return json.load(f)

materials = load_json('game_systems/data/materials.json')
monsters = load_json('game_systems/data/monsters.json')
locations = load_json('game_systems/data/adventure_locations.json')

def get_item_value(item_id):
    if item_id in materials:
        return materials[item_id].get('value', 0)
    return 0

def calc_monster_ev(monster_id):
    if monster_id not in monsters:
        return 0
    m = monsters[monster_id]
    ev = 0
    if 'drops' in m:
        for drop in m['drops']:
            if len(drop) == 2:
                item, drop_rate = drop
                ev += get_item_value(item) * (drop_rate / 100.0)
    return ev

def calc_gather_ev(gatherables):
    ev_sum = 0
    total_weight = 0
    if not gatherables:
        return 0
    for gather in gatherables:
        if len(gather) == 2:
            item_id, weight = gather
            ev_sum += get_item_value(item_id) * weight
            total_weight += weight
    return ev_sum / total_weight if total_weight > 0 else 0

def main():
    print("Location Economy Analysis:")
    print(f"{'Location Name':<30} | {'Rank':<4} | {'Lvl':<3} | {'Kill EV':<8} | {'Gather EV':<9} | {'Est EV/Trip (30m)'}")
    print("-" * 80)

    results = []
    for loc_id, loc in locations.items():
        if loc_id == 'guild_arena':
            continue

        # Monster EV
        ev_sum = 0
        total_weight = 0
        for m in loc.get('monsters', []):
            if len(m) == 2:
                m_id, weight = m
                ev_sum += calc_monster_ev(m_id) * weight
                total_weight += weight
        kill_ev = ev_sum / total_weight if total_weight > 0 else 0

        # Gather EV
        gather_ev = calc_gather_ev(loc.get('gatherables', []))

        # Estimated EV per 30m trip (Roughly 10 kills, 3 gathers)
        est_trip_ev = (kill_ev * 10) + (gather_ev * 3)

        results.append({
            'name': loc.get('name', loc_id),
            'rank': loc.get('min_rank', '-'),
            'level': loc.get('level_req', 0),
            'kill_ev': kill_ev,
            'gather_ev': gather_ev,
            'est_trip_ev': est_trip_ev
        })

    results.sort(key=lambda x: x['level'])

    for res in results:
        print(f"{res['name']:<30} | {res['rank']:<4} | {res['level']:<3} | {res['kill_ev']:>8.2f} | {res['gather_ev']:>9.2f} | {res['est_trip_ev']:>8.2f}")

if __name__ == "__main__":
    main()
