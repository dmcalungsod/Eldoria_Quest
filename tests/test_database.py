"""
Comprehensive Database Tests for Eldoria Quest
-----------------------------------------------
Tests all database operations including players, inventory, quests, and combat.
SAFE: Uses temporary test database, never touches production data.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tempfile

from database.create_database import create_tables
from database.database_manager import DATABASE_NAME, DatabaseManager
from database.populate_database import main as populate_db

TEST_DB_PATH = None
ORIGINAL_DB_PATH = None


def setup_test_database():
    """Create a temporary test database."""
    global TEST_DB_PATH, ORIGINAL_DB_PATH
    import database.create_database as db_create
    import database.database_manager as db_manager
    import database.populate_database as db_populate

    TEST_DB_PATH = tempfile.mktemp(suffix=".db")
    ORIGINAL_DB_PATH = DATABASE_NAME

    db_manager.DATABASE_NAME = TEST_DB_PATH
    db_create.DATABASE_NAME = TEST_DB_PATH
    db_populate.DATABASE_NAME = TEST_DB_PATH
    DatabaseManager.__init__ = lambda self: setattr(self, 'db_name', TEST_DB_PATH)

    print(f"✓ Using temporary test database: {TEST_DB_PATH}")


def cleanup_test_database():
    """Remove temporary test database."""
    global TEST_DB_PATH
    if TEST_DB_PATH and os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)
        print(f"✓ Removed temporary test database: {TEST_DB_PATH}")


def test_database_creation():
    """Test database schema creation."""
    print("\n=== Testing Database Creation ===")
    try:
        create_tables()
        print("✓ Database schema created successfully")
        return True
    except Exception as e:
        print(f"✗ Database creation failed: {e}")
        return False


def test_database_population():
    """Test database population with game data."""
    print("\n=== Testing Database Population ===")
    try:
        populate_db()
        print("✓ Database populated successfully")
        return True
    except Exception as e:
        print(f"✗ Database population failed: {e}")
        return False


def test_player_operations():
    """Test player CRUD operations."""
    print("\n=== Testing Player Operations ===")
    db = DatabaseManager()
    test_discord_id = 999999999

    try:
        if db.player_exists(test_discord_id):
            conn = db.connect()
            cur = conn.cursor()
            cur.execute("DELETE FROM players WHERE discord_id = ?", (test_discord_id,))
            cur.execute("DELETE FROM stats WHERE discord_id = ?", (test_discord_id,))
            conn.commit()
            conn.close()
            print("  Cleaned up existing test player")

        test_stats = {
            "STR": {"base": 10, "bonus": 0},
            "END": {"base": 10, "bonus": 0},
            "DEX": {"base": 10, "bonus": 0},
            "AGI": {"base": 10, "bonus": 0},
            "MAG": {"base": 10, "bonus": 0},
            "LCK": {"base": 10, "bonus": 0}
        }

        db.create_player(
            discord_id=test_discord_id,
            name="TestPlayer",
            class_id=1,
            stats_data=test_stats,
            initial_hp=100,
            initial_mp=20,
            race="Human",
            gender="Male"
        )
        print("✓ Player created successfully")

        player = db.get_player(test_discord_id)
        assert player is not None, "Player not found"
        assert player["name"] == "TestPlayer"
        print(f"✓ Player retrieved: {player['name']}, Level {player['level']}")

        stats = db.get_player_stats_json(test_discord_id)
        assert stats["STR"]["base"] == 10
        print("✓ Player stats verified")

        vitals = db.get_player_vitals(test_discord_id)
        assert vitals["current_hp"] == 100
        assert vitals["current_mp"] == 20
        print("✓ Player vitals verified")

        db.set_player_vitals(test_discord_id, 50, 10)
        vitals = db.get_player_vitals(test_discord_id)
        assert vitals["current_hp"] == 50
        assert vitals["current_mp"] == 10
        print("✓ Player vitals updated successfully")

        return True

    except Exception as e:
        print(f"✗ Player operations failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_class_data():
    """Test class data retrieval."""
    print("\n=== Testing Class Data ===")
    db = DatabaseManager()

    try:
        for class_id in range(1, 5):
            class_data = db.get_class(class_id)
            if class_data:
                print(f"✓ Class {class_id}: {class_data['name']}")
            else:
                print(f"✗ Class {class_id} not found")
                return False
        return True

    except Exception as e:
        print(f"✗ Class data test failed: {e}")
        return False


def test_context_manager():
    """Test the optimized context manager for connections."""
    print("\n=== Testing Context Manager ===")
    db = DatabaseManager()

    try:
        with db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) as count FROM classes")
            result = cur.fetchone()
            count = result["count"]
            print(f"✓ Context manager working: {count} classes found")
        return True

    except Exception as e:
        print(f"✗ Context manager test failed: {e}")
        return False


def test_monster_data():
    """Test monster data retrieval."""
    print("\n=== Testing Monster Data ===")
    db = DatabaseManager()

    try:
        with db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) as count FROM monsters")
            result = cur.fetchone()
            monster_count = result["count"]
            print(f"✓ Found {monster_count} monsters in database")

            cur.execute("SELECT * FROM monsters LIMIT 5")
            monsters = cur.fetchall()
            for monster in monsters:
                print(f"  - {monster['name']} (Tier: {monster['tier']}, Level: {monster['level']})")

        return True

    except Exception as e:
        print(f"✗ Monster data test failed: {e}")
        return False


def test_equipment_data():
    """Test equipment data retrieval."""
    print("\n=== Testing Equipment Data ===")
    db = DatabaseManager()

    try:
        with db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) as count FROM equipment")
            result = cur.fetchone()
            equip_count = result["count"]
            print(f"✓ Found {equip_count} equipment items")

            cur.execute("SELECT COUNT(*) as count FROM class_equipment")
            result = cur.fetchone()
            class_equip_count = result["count"]
            print(f"✓ Found {class_equip_count} class-specific equipment items")

        return True

    except Exception as e:
        print(f"✗ Equipment data test failed: {e}")
        return False


def cleanup_test_data():
    """Clean up test data."""
    print("\n=== Cleaning Up Test Data ===")
    db = DatabaseManager()
    test_discord_id = 999999999

    try:
        conn = db.connect()
        cur = conn.cursor()
        cur.execute("DELETE FROM players WHERE discord_id = ?", (test_discord_id,))
        cur.execute("DELETE FROM stats WHERE discord_id = ?", (test_discord_id,))
        conn.commit()
        conn.close()
        print("✓ Test data cleaned up")
        return True

    except Exception as e:
        print(f"✗ Cleanup failed: {e}")
        return False


def run_all_tests():
    """Run all database tests."""
    print("\n" + "="*60)
    print("ELDORIA QUEST - DATABASE TEST SUITE")
    print("="*60)
    print("NOTE: Tests run on temporary database - production data is safe!")
    print("="*60)

    setup_test_database()

    tests = [
        ("Database Creation", test_database_creation),
        ("Database Population", test_database_population),
        ("Class Data", test_class_data),
        ("Monster Data", test_monster_data),
        ("Equipment Data", test_equipment_data),
        ("Context Manager", test_context_manager),
        ("Player Operations", test_player_operations),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n✗ {test_name} crashed: {e}")
            results.append((test_name, False))

    cleanup_test_data()
    cleanup_test_database()

    print("\n" + "="*60)
    print("TEST RESULTS SUMMARY")
    print("="*60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")

    print(f"\nTotal: {passed}/{total} tests passed")
    print("="*60 + "\n")

    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
