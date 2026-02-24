import json
import os
import sys

# Add repo root to path
sys.path.append(os.getcwd())

try:
    from game_systems.data.materials import MATERIALS
    from game_systems.data.skills_data import SKILLS
    from game_systems.monsters.monster_skills import MONSTER_SKILLS
except ImportError as e:
    print(f"Import Error: {e}")
    sys.exit(1)

# Load Monsters
try:
    with open("game_systems/data/monsters.json") as f:
        monsters = json.load(f)
except json.JSONDecodeError as e:
    print(f"JSON Error: {e}")
    sys.exit(1)

errors = []

for m_id, data in monsters.items():
    # Check Skills
    for skill in data.get("skills", []):
        if skill not in MONSTER_SKILLS and skill not in SKILLS:
            errors.append(f"Monster {m_id} uses unknown skill: {skill}")

    # Check Drops
    for drop_tuple in data.get("drops", []):
        item_key = drop_tuple[0]
        if item_key not in MATERIALS:
            errors.append(f"Monster {m_id} drops unknown item: {item_key}")

if errors:
    print("Verification Failed:")
    for err in errors:
        print(err)
    sys.exit(1)
else:
    print("All verifications passed!")
