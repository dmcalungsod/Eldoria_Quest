import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from game_systems.data.adventure_locations import LOCATIONS
from game_systems.data.materials import MATERIALS
from game_systems.data.monsters import MONSTERS
from scripts.analysis.economy_utils import calculate_expected_value_stats

def main():
    zones = ["shrouded_fen", "clockwork_halls", "celestial_archipelago", "shimmering_wastes", "silent_city_ouros"]

    print("Deep Dive: Specific Zone Economy Gaps")
    print("-" * 60)

    for zone_id in zones:
        data = LOCATIONS.get(zone_id)
        if not data:
            print(f"Zone {zone_id} not found.")
            continue

        stats = calculate_expected_value_stats(data, player_luck=10)
        print(f"\n{data['name']} (Level {data.get('level_req')}, Rank {data.get('min_rank')})")
        print(f"  Total EV/Hr: {stats['total_hourly']:.1f}")
        print(f"  Aurum/Hr (Combat): {stats['hourly_aurum']:.1f}")
        print(f"  Material/Hr (Gathering + Drops): {stats['hourly_materials']:.1f}")

        # Gathering Details
        print("  Gathering Sources:")
        gatherables = data.get("gatherables", {})
        if isinstance(gatherables, dict):
            total_gather_weight = sum(gatherables.values())
            for mat_id, weight in gatherables.items():
                mat_val = MATERIALS.get(mat_id, {}).get("value", 0)
                prob = weight / total_gather_weight if total_gather_weight > 0 else 0
                ev_per_gather = prob * mat_val
                print(f"    - {mat_id}: {prob*100:.1f}% chance, Value {mat_val} -> {ev_per_gather:.1f} EV/gather")
        elif isinstance(gatherables, list):
            total_gather_weight = sum([item[1] for item in gatherables])
            for item in gatherables:
                mat_id = item[0]
                weight = item[1]
                mat_val = MATERIALS.get(mat_id, {}).get("value", 0)
                prob = weight / total_gather_weight if total_gather_weight > 0 else 0
                ev_per_gather = prob * mat_val
                print(f"    - {mat_id}: {prob*100:.1f}% chance, Value {mat_val} -> {ev_per_gather:.1f} EV/gather")

        # Monster Details
        print("  Monster Sources:")
        monsters = data.get("monsters", [])
        total_mob_weight = sum([item[1] for item in monsters])
        for item in monsters:
            mob_id = item[0]
            weight = item[1]
            mob = MONSTERS.get(mob_id, {})
            prob = weight / total_mob_weight if total_mob_weight > 0 else 0

            drop_ev = 0
            for drop_id, chance in mob.get("drops", []):
                drop_val = MATERIALS.get(drop_id, {}).get("value", 0)
                drop_ev += (chance / 100) * drop_val

            aurum_min, aurum_max = mob.get("aurum_drop", [0, 0])
            avg_aurum = (aurum_min + aurum_max) / 2

            total_mob_ev = avg_aurum + drop_ev
            print(f"    - {mob_id}: {prob*100:.1f}% chance, Aurum {avg_aurum:.1f}, Drops {drop_ev:.1f} -> {total_mob_ev:.1f} Total EV/kill")

if __name__ == "__main__":
    main()
