import os

files = [
    "tests/test_world_events.py",
    "tests/test_db_purchase.py",
    "tests/test_infirmary_security.py",
    "tests/test_stack_limits.py",
    "tests/test_vitals_concurrency.py",
    "tests/test_equipment_stack_split.py",
    "tests/test_monster_data.py",
    "tests/test_adventure_session_concurrency.py",
    "tests/test_shop_integration.py",
    "tests/test_infirmary_fallback.py",
    "tests/test_infirmary_exploit.py",
    "tests/test_adventure_day_night.py",
    "tests/test_shop_stale_state.py",
    "tests/test_quest_security.py",
    "tests/test_harvest_event.py"
]

target_str = "sys.path.append(os.getcwd())"
replacement_str = "sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))"

for filepath in files:
    with open(filepath, "r") as f:
        content = f.read()

    if target_str in content:
        new_content = content.replace(target_str, replacement_str)
        # Also remove any try/except blocks around imports that use sys.exit(1)
        # This is harder to do via simple replace, but the grep didn't find sys.exit(1) other than the one I fixed?
        # Wait, the grep output for sys.exit(1) was empty!
        # But I should double check if they have the fragile try/except block.

        with open(filepath, "w") as f:
            f.write(new_content)
        print(f"Fixed {filepath}")
    else:
        print(f"Skipped {filepath} (pattern not found)")
