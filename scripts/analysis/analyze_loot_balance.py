import json
import logging
import sys
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# Adjust path to find the module
sys.path.append(str(Path(__file__).parents[2]))

try:
    from game_systems.data.materials import MATERIALS  # noqa: E402
except ImportError:
    logging.error("Failed to import MATERIALS. Ensure you are running from the repo root.")
    sys.exit(1)


# Helper functions
def calculate_combat_power(hp, atk, defense):
    # Simple CP metric: Effective HP * DPS potential
    # Defense reduces incoming damage. Let's assume player damage is constant for relative comparison.
    # Actually, let's use a simpler heuristic: HP * Atk * (1 + Def/100)
    return hp * atk * (1 + defense / 100)


def calculate_expected_loot_value(drops, materials):
    total_value = 0
    for drop in drops:
        item_id = drop[0]
        chance = drop[1]

        # Get value
        if item_id in materials:
            value = materials[item_id].get("value", 0)
        else:
            # Fallback or check if it's a known consumable/equipment
            # For this analysis, we focus on material drops as primary income
            # Consumables usually sell for less, let's estimate 10g for unknown items
            value = 10
            # logging.warning(f"Unknown item value: {item_id}, assuming {value}g")

        total_value += (chance / 100) * value
    return total_value


def analyze():
    # Load Data
    data_dir = Path("game_systems/data")
    monsters_path = data_dir / "monsters.json"
    locations_path = data_dir / "adventure_locations.json"

    with open(monsters_path, encoding='utf-8') as f:
        monsters = json.load(f)

    with open(locations_path, encoding='utf-8') as f:
        locations = json.load(f)

    # Analyze Monsters
    monster_stats = {}
    for mid, m in monsters.items():
        cp = calculate_combat_power(m['hp'], m['atk'], m.get('def', 0))
        elv = calculate_expected_loot_value(m.get('drops', []), MATERIALS)
        efficiency = elv / cp if cp > 0 else 0

        monster_stats[mid] = {
            "name": m['name'],
            "tier": m.get('tier', 'Normal'),
            "cp": cp,
            "elv": elv,
            "efficiency": efficiency
        }

    # Analyze Locations
    location_stats = {}
    for lid, loc in locations.items():
        if lid == "guild_arena":
            continue  # Skip arena

        monsters_list = loc.get('monsters', [])
        if not monsters_list:
            continue

        total_cp = 0
        total_elv = 0
        count = 0

        # Weighted average based on spawn chance (simple average if weights not normalized)
        # The list is [[id, weight], ...]
        # Let's normalize weights
        total_weight = sum(m[1] for m in monsters_list)

        for m_entry in monsters_list:
            m_key = m_entry[0]
            weight = m_entry[1]

            if m_key not in monster_stats:
                logging.warning(f"Monster {m_key} not found in monster stats")
                continue

            stats = monster_stats[m_key]
            normalized_weight = weight / total_weight if total_weight > 0 else 0

            total_cp += stats['cp'] * normalized_weight
            total_elv += stats['elv'] * normalized_weight
            count += 1

        avg_efficiency = total_elv / total_cp if total_cp > 0 else 0

        location_stats[lid] = {
            "name": loc['name'],
            "rank": loc.get('min_rank', '?'),
            "level": loc.get('level_req', 0),
            "avg_cp": total_cp,
            "avg_elv": total_elv,
            "efficiency": avg_efficiency
        }

    # Generate Report
    report = ["# 📊 Loot Economy Analysis Report — 2026-03-01\n"]
    report.append("**Data Sources:** `monsters.json`, `adventure_locations.json`, `materials.py`\n")

    report.append("## 🌍 Location Analysis (Risk vs Reward)\n")
    report.append("| Location | Rank | Level | Avg Combat Power | Avg Loot Value (Gold) | Efficiency (Gold/CP) |")
    report.append("| :--- | :---: | :---: | :---: | :---: | :---: |")

    # Sort by Level
    sorted_locs = sorted(location_stats.items(), key=lambda x: x[1]['level'])

    for lid, stats in sorted_locs:
        report.append(f"| **{stats['name']}** | {stats['rank']} | {stats['level']} | {stats['avg_cp']:.0f} | {stats['avg_elv']:.1f}g | {stats['efficiency']*1000:.2f} |")

    report.append("\n## 🔍 Deep Dive: Deepgrove Roots vs Shrouded Fen\n")

    dg = location_stats.get('deepgrove_roots')
    sf = location_stats.get('shrouded_fen')

    if dg and sf:
        report.append(f"- **Deepgrove Roots (Rank {dg['rank']}):** {dg['avg_elv']:.1f}g / {dg['avg_cp']:.0f} CP = **{dg['efficiency']*1000:.2f}** eff")
        report.append(f"- **Shrouded Fen (Rank {sf['rank']}):** {sf['avg_elv']:.1f}g / {sf['avg_cp']:.0f} CP = **{sf['efficiency']*1000:.2f}** eff")

        if dg['efficiency'] > sf['efficiency']:
            ratio = dg['efficiency'] / sf['efficiency']
            report.append(f"\n**⚠️ IMBALANCE DETECTED:** Lower-rank zone `Deepgrove Roots` is **{ratio:.1f}x** more efficient than higher-rank `Shrouded Fen`. Players are incentivized to farm the easier zone.")
        else:
            report.append("\n**✅ BALANCE OK:** Higher-rank zone offers better efficiency.")

    report.append("\n## 🚨 Outliers & Anomalies (Top 10 Efficient Monsters)\n")
    # Check for monsters with very high efficiency (Low CP, High Gold)
    sorted_monsters = sorted(monster_stats.items(), key=lambda x: x[1]['efficiency'], reverse=True)

    report.append("| Monster | Tier | CP | Loot Value | Efficiency |")
    report.append("| :--- | :---: | :---: | :---: | :---: |")
    for mid, stats in sorted_monsters[:10]:
        report.append(f"| {stats['name']} | {stats['tier']} | {stats['cp']:.0f} | {stats['elv']:.1f}g | {stats['efficiency']*1000:.2f} |")

    # Save Report
    output_path = Path(".Jules/analysis/2026-03-01_loot_economy_analysis.md")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(report))

    print(f"Report generated at {output_path}")
    print("\n".join(report))  # Print to stdout for agent review


if __name__ == "__main__":
    analyze()
