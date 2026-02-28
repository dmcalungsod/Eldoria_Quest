"""
tests/verify_alchemist_gear.py

Verification script to ensure:
1. Alchemist class equipment is generated correctly.
2. 'alchemist_coat' items exist and have correct stats.
3. Alchemist class can equip these items.
"""

import os
import sys

# Mock pymongo to allow import of EquipmentManager
from unittest.mock import MagicMock

sys.modules['pymongo'] = MagicMock()
sys.modules['pymongo.errors'] = MagicMock()

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from game_systems.data.class_data import CLASSES
from game_systems.data.class_equipments import CLASS_EQUIPMENTS

# Import EquipmentManager after mocking pymongo
from game_systems.items.equipment_manager import EquipmentManager


def verify_alchemist_generation():
    print("--- Verifying Alchemist Equipment Generation ---")

    alchemist_items = []
    for key, item in CLASS_EQUIPMENTS.items():
        if item.get("class") == "Alchemist":
            alchemist_items.append(item)

    if not alchemist_items:
        print("FAIL: No Alchemist items generated in CLASS_EQUIPMENTS.")
        return False

    print(f"PASS: Found {len(alchemist_items)} Alchemist items.")

    # Verify specific slots
    slots_found = set(item["slot"] for item in alchemist_items)
    required_slots = {
        "mace", "dagger", "tome", "hood", "alchemist_coat",
        "gloves", "legs", "boots", "belt", "accessory",
        "medium_armor", "medium_gloves", "medium_legs", "medium_boots", "leather_cap", "robe"
    }

    missing_slots = required_slots - slots_found
    if missing_slots:
        print(f"FAIL: Missing slots for Alchemist: {missing_slots}")
        return False

    print(f"PASS: All required Alchemist slots generated: {slots_found}")

    # Verify Alchemist Coat stats
    coats = [item for item in alchemist_items if item["slot"] == "alchemist_coat"]
    if not coats:
        print("FAIL: No 'alchemist_coat' items found.")
        return False

    # Check at least one coat has the right stats
    # Stat budget: MAG, DEX, END
    valid_coats = 0
    for coat in coats:
        stats = coat["stats_bonus"]
        # Just check keys existence
        if "MAG" in stats and "DEX" in stats and "END" in stats:
            valid_coats += 1
        else:
            print(f"WARNING: Coat {coat['name']} missing expected stat keys: {stats.keys()}")

    if valid_coats == 0:
        print("FAIL: No valid alchemist coats found.")
        return False

    print(f"PASS: Verified {valid_coats} Alchemist Coats have correct stat distribution keys.")
    return True

def verify_equip_logic():
    print("\n--- Verifying Equip Logic ---")

    # Check Allowed Slots in Class Data
    alchemist_class = CLASSES.get("Alchemist")
    if not alchemist_class:
        print("FAIL: Alchemist class not found in CLASS_DATA.")
        return False

    allowed_slots = alchemist_class.get("allowed_slots", [])
    if "alchemist_coat" not in allowed_slots:
         print("FAIL: 'alchemist_coat' not in Alchemist allowed_slots.")
         return False

    if "tome" not in allowed_slots:
         print("FAIL: 'tome' not in Alchemist allowed_slots.")
         return False

    print("PASS: Alchemist class has correct allowed_slots.")

    # Check Body Slot conflict logic in EquipmentManager
    if "alchemist_coat" not in EquipmentManager.BODY_SLOTS:
        print("FAIL: 'alchemist_coat' not in EquipmentManager.BODY_SLOTS.")
        return False

    print("PASS: 'alchemist_coat' correctly registered as BODY_SLOTS.")

    return True

if __name__ == "__main__":
    gen_ok = verify_alchemist_generation()
    logic_ok = verify_equip_logic()

    if gen_ok and logic_ok:
        print("\n✅ SUCCESS: Alchemist Gear Implementation Verified.")
        sys.exit(0)
    else:
        print("\n❌ FAILURE: Issues detected.")
        sys.exit(1)
