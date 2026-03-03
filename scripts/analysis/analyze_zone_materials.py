import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from game_systems.data.adventure_locations import LOCATIONS
from game_systems.data.materials import MATERIALS
from game_systems.data.monsters import MONSTERS

def main():
    print("Zone Economy Analysis")
    print("-" * 50)

    sorted_locations = sorted(LOCATIONS.items(), key=lambda x: x[1].get("level_req", 0))
    for key, data in sorted_locations:
        if key == "guild_arena":
            continue

        print(f"\n{data['name']} (Level {data.get('level_req')}, Rank {data.get('min_rank')})")

        # Analyze Gatherables
        gatherables = data.get("gatherables", [])
        if gatherables:
            print("  Gatherables:")
            for item in gatherables:
                mat_id = item[0]
                weight = item[1]
                mat_name = MATERIALS.get(mat_id, {}).get("name", mat_id)
                mat_val = MATERIALS.get(mat_id, {}).get("value", 0)
                print(f"    - {mat_name} (Value: {mat_val}) - {weight} weight")
        else:
            print("  Gatherables: None")

        # Analyze Monsters
        monsters = data.get("monsters", [])
        if monsters:
            print("  Monsters:")
            for item in monsters:
                mob_id = item[0]
                weight = item[1]
                mob = MONSTERS.get(mob_id, {})
                mob_name = mob.get("name", mob_id)
                mob_lvl = mob.get("level", 0)

                drops = []
                for drop_id, chance in mob.get("drops", []):
                    drop_val = MATERIALS.get(drop_id, {}).get("value", 0)
                    drops.append(f"{drop_id}({chance}%:{drop_val}g)")

                print(f"    - {mob_name} (Lvl {mob_lvl}) - {weight} weight - Drops: {', '.join(drops)}")

if __name__ == "__main__":
    main()
