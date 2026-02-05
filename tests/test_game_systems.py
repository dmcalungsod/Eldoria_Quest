"""
Game Systems Tests for Eldoria Quest
-------------------------------------
Tests combat, inventory, and player progression systems.
SAFE: Uses temporary test database, never touches production data.
"""

import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.database_manager import DatabaseManager
from game_systems.combat.combat_engine import CombatEngine
from game_systems.combat.damage_formula import DamageFormula
from game_systems.items.equipment_manager import EquipmentManager
from game_systems.items.inventory_manager import InventoryManager
from game_systems.player.level_up import LevelUpSystem
from game_systems.player.player_stats import PlayerStats

TEST_DB_PATH = None


def setup_test_database():
    """Create a temporary test database."""
    global TEST_DB_PATH
    import database.create_database as db_create
    import database.database_manager as db_manager
    import database.populate_database as db_populate

    TEST_DB_PATH = tempfile.mktemp(suffix=".db")

    # Patch paths
    db_manager.DATABASE_NAME = TEST_DB_PATH
    db_create.DATABASE_NAME = TEST_DB_PATH
    db_populate.DATABASE_NAME = TEST_DB_PATH

    DatabaseManager.__init__ = lambda self: setattr(self, "db_name", TEST_DB_PATH)

    print(f"✓ Using temporary test database: {TEST_DB_PATH}")


def cleanup_test_database():
    """Remove temporary test database."""
    global TEST_DB_PATH
    if TEST_DB_PATH and os.path.exists(TEST_DB_PATH):
        try:
            os.remove(TEST_DB_PATH)
            print(f"✓ Removed temporary test database: {TEST_DB_PATH}")
        except PermissionError:
            pass


def setup_test_environment():
    """Set up test environment with database and test player."""
    print("\n=== Setting Up Test Environment ===")

    import database.create_database as db_create
    import database.populate_database as db_populate

    db_create.create_tables()
    db_populate.main()

    db = DatabaseManager()
    test_discord_id = 888888888

    # FIX: Use get_connection context manager
    with db.get_connection() as conn:
        conn.execute("DELETE FROM inventory WHERE discord_id = ?", (test_discord_id,))
        conn.execute("DELETE FROM players WHERE discord_id = ?", (test_discord_id,))
        conn.execute("DELETE FROM stats WHERE discord_id = ?", (test_discord_id,))

    test_stats = {
        "STR": {"base": 15, "bonus": 0},
        "END": {"base": 12, "bonus": 0},
        "DEX": {"base": 10, "bonus": 0},
        "AGI": {"base": 8, "bonus": 0},
        "MAG": {"base": 5, "bonus": 0},
        "LCK": {"base": 10, "bonus": 0},
    }

    db.create_player(
        discord_id=test_discord_id,
        name="TestWarrior",
        class_id=1,
        stats_data=test_stats,
        initial_hp=150,
        initial_mp=30,
        race="Human",
        gender="Male",
    )

    print("✓ Test environment ready")
    return test_discord_id


def test_player_stats():
    """Test PlayerStats class."""
    print("\n=== Testing PlayerStats ===")

    try:
        stats = PlayerStats(str_base=15, end_base=12, dex_base=10, agi_base=8, mag_base=5, lck_base=10)

        print(f"✓ PlayerStats created: STR={stats.strength}, END={stats.endurance}")
        print(f"  Max HP: {stats.max_hp}, Max MP: {stats.max_mp}")

        stats.add_bonus_stat("STR", 5)
        assert stats.strength == 20, "Bonus stat not added correctly"
        print("✓ Bonus stats working correctly")

        stats_dict = stats.to_dict()
        restored_stats = PlayerStats.from_dict(stats_dict)
        assert restored_stats.strength == 20
        print("✓ Serialization/deserialization working")

        return True

    except Exception as e:
        print(f"✗ PlayerStats test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_inventory_system(test_discord_id):
    """Test inventory operations."""
    print("\n=== Testing Inventory System ===")
    db = DatabaseManager()
    inv_manager = InventoryManager(db)

    try:
        inv_manager.add_item(
            discord_id=test_discord_id,
            item_key="test_sword",
            item_name="Test Sword",
            item_type="equipment",
            rarity="Uncommon",
            amount=1,
            slot="sword",  # FIX: Use valid lowercase slot key
            item_source_table="equipment",
        )
        print("✓ Item added to inventory")

        inventory = inv_manager.get_inventory(test_discord_id)
        assert len(inventory) > 0, "Inventory is empty"
        print(f"✓ Retrieved inventory: {len(inventory)} items")

        inv_manager.add_item(
            discord_id=test_discord_id,
            item_key="health_potion",
            item_name="Health Potion",
            item_type="consumable",
            rarity="Common",
            amount=5,
        )
        print("✓ Consumable added to inventory")

        return True

    except Exception as e:
        print(f"✗ Inventory test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_equipment_system(test_discord_id):
    """Test equipment and stat recalculation."""
    print("\n=== Testing Equipment System ===")
    db = DatabaseManager()
    equip_manager = EquipmentManager(db)
    inv_manager = InventoryManager(db)

    try:
        # Ensure there's a weapon in the DB to give
        with db.get_connection() as conn:
            cur = conn.execute("SELECT * FROM equipment WHERE slot = 'sword' LIMIT 1")
            weapon = cur.fetchone()

            if weapon:
                inv_manager.add_item(
                    discord_id=test_discord_id,
                    item_key=str(weapon["id"]),
                    item_name=weapon["name"],
                    item_type="equipment",
                    rarity=weapon["rarity"],
                    amount=1,
                    slot=weapon["slot"],
                    item_source_table="equipment",
                )
                print(f"✓ Added {weapon['name']} to inventory")
            else:
                print("⚠ No sword found in DB, skipping equip test.")

        # Force recalculation
        recalc_stats = equip_manager.recalculate_player_stats(test_discord_id)
        print("✓ Recalculated stats working")
        print(f"  Max HP: {recalc_stats.max_hp}")

        return True

    except Exception as e:
        print(f"✗ Equipment test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_combat_system(test_discord_id):
    """Test combat engine."""
    print("\n=== Testing Combat System ===")
    db = DatabaseManager()

    try:
        stats_json = db.get_player_stats_json(test_discord_id)
        player_stats = PlayerStats.from_dict(stats_json)

        player = db.get_player(test_discord_id)
        player_wrapper = LevelUpSystem(
            stats=player_stats, level=player["level"], exp=player["experience"], exp_to_next=player["exp_to_next"]
        )
        player_wrapper.hp_current = 150

        test_monster = {"name": "Test Goblin", "HP": 50, "ATK": 10, "DEF": 5, "DEX": 8, "MAG": 0, "Level": 1, "EXP": 20}

        engine = CombatEngine(
            player=player_wrapper, monster=test_monster, player_skills=[], player_mp=30, player_class_id=1
        )

        result = engine.run_combat_turn()
        print("✓ Combat turn executed")
        print(f"  Player HP: {result['hp_current']}")

        return True

    except Exception as e:
        print(f"✗ Combat test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_damage_formulas():
    """Test damage calculation formulas."""
    print("\n=== Testing Damage Formulas ===")

    try:
        player_stats = PlayerStats(str_base=15, end_base=12, dex_base=10, agi_base=8, mag_base=5, lck_base=10)
        monster = {"DEF": 5, "Level": 1}

        damage, crit, _ = DamageFormula.player_attack(player_stats, monster)
        print(f"✓ Basic attack: {damage} damage, Crit: {crit}")

        test_skill = {"key_id": "power_strike", "name": "Power Strike", "power_multiplier": 1.5, "mp_cost": 10}
        skill_damage, skill_crit, _ = DamageFormula.player_skill(player_stats, monster, test_skill, skill_level=1)
        print(f"✓ Skill attack: {skill_damage} damage, Crit: {skill_crit}")

        return True

    except Exception as e:
        print(f"✗ Damage formula test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_level_up_system(test_discord_id):
    """Test level-up and experience system."""
    print("\n=== Testing Level-Up System ===")
    db = DatabaseManager()

    try:
        player = db.get_player(test_discord_id)
        stats_json = db.get_player_stats_json(test_discord_id)
        player_stats = PlayerStats.from_dict(stats_json)

        level_system = LevelUpSystem(
            stats=player_stats, level=player["level"], exp=player["experience"], exp_to_next=player["exp_to_next"]
        )

        level_system.add_exp(150)
        print(f"✓ Added 150 EXP. New Level: {level_system.level}")
        return True

    except Exception as e:
        print(f"✗ Level-up test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def cleanup_test_data(test_discord_id):
    """Clean up test data."""
    print("\n=== Cleaning Up Test Data ===")
    db = DatabaseManager()
    try:
        with db.get_connection() as conn:
            # Delete children first
            conn.execute("DELETE FROM inventory WHERE discord_id = ?", (test_discord_id,))
            conn.execute("DELETE FROM stats WHERE discord_id = ?", (test_discord_id,))
            conn.execute("DELETE FROM player_skills WHERE discord_id = ?", (test_discord_id,))

            # Delete parent last
            conn.execute("DELETE FROM players WHERE discord_id = ?", (test_discord_id,))

        print("✓ Test data cleaned up")
        return True
    except Exception as e:
        print(f"✗ Cleanup failed: {e}")
        return False


def run_all_tests():
    print("\n" + "=" * 60)
    print("ELDORIA QUEST - GAME SYSTEMS TEST SUITE")
    print("=" * 60)

    setup_test_database()
    test_discord_id = setup_test_environment()

    tests = [
        ("PlayerStats", lambda: test_player_stats()),
        ("Inventory System", lambda: test_inventory_system(test_discord_id)),
        ("Equipment System", lambda: test_equipment_system(test_discord_id)),
        ("Damage Formulas", lambda: test_damage_formulas()),
        ("Combat System", lambda: test_combat_system(test_discord_id)),
        ("Level-Up System", lambda: test_level_up_system(test_discord_id)),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n✗ {test_name} crashed: {e}")
            results.append((test_name, False))

    cleanup_test_data(test_discord_id)
    cleanup_test_database()

    passed = sum(1 for _, result in results if result)
    total = len(results)

    print("\n" + "=" * 60)
    print(f"TEST RESULTS: {passed}/{total} Passed")
    print("=" * 60 + "\n")

    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
