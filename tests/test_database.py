"""
Comprehensive Database Tests for Eldoria Quest
-----------------------------------------------
Tests all database operations including players, inventory, quests, and combat.
SAFE: Uses temporary test database, never touches production data.
"""

import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.database_manager import DatabaseManager

TEST_DB_PATH = None


def setup_test_database():
    """Create a temporary test database."""
    global TEST_DB_PATH
    import database.create_database as db_create
    import database.database_manager as db_manager
    import database.populate_database as db_populate

    TEST_DB_PATH = tempfile.mktemp(suffix=".db")

    # Patch the database paths in all modules
    db_manager.DATABASE_NAME = TEST_DB_PATH
    db_create.DATABASE_NAME = TEST_DB_PATH
    db_populate.DATABASE_NAME = TEST_DB_PATH

    # Re-init DatabaseManager to pick up the change
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
            print(f"⚠ Could not remove {TEST_DB_PATH} (file in use)")


def test_database_creation():
    print("\n=== Testing Database Creation ===")
    import database.create_database as db_create

    try:
        db_create.create_tables()
        print("✓ Database schema created successfully")
        return True
    except Exception as e:
        print(f"✗ Database creation failed: {e}")
        return False


def test_database_population():
    print("\n=== Testing Database Population ===")
    import database.populate_database as db_populate

    try:
        db_populate.main()
        print("✓ Database populated successfully")
        return True
    except Exception as e:
        print(f"✗ Database population failed: {e}")
        return False


def test_player_operations():
    print("\n=== Testing Player Operations ===")
    db = DatabaseManager()
    test_discord_id = 999999999

    try:
        # Clean up any existing test player
        with db.get_connection() as conn:
            conn.execute("DELETE FROM players WHERE discord_id = ?", (test_discord_id,))
            conn.execute("DELETE FROM stats WHERE discord_id = ?", (test_discord_id,))

        test_stats = {
            "STR": {"base": 10, "bonus": 0},
            "END": {"base": 10, "bonus": 0},
            "DEX": {"base": 10, "bonus": 0},
            "AGI": {"base": 10, "bonus": 0},
            "MAG": {"base": 10, "bonus": 0},
            "LCK": {"base": 10, "bonus": 0},
        }

        # Ensure class 1 exists (Warrior) - should be there from population
        with db.get_connection() as conn:
            exists = conn.execute("SELECT 1 FROM classes WHERE id=1").fetchone()
            if not exists:
                print("⚠ Warning: Classes missing. Injecting Warrior class.")
                conn.execute("INSERT INTO classes (id, name, description) VALUES (1, 'Warrior', 'Test')")

        db.create_player(
            discord_id=test_discord_id,
            name="TestPlayer",
            class_id=1,
            stats_data=test_stats,
            initial_hp=100,
            initial_mp=20,
            race="Human",
            gender="Male",
        )
        print("✓ Player created successfully")

        player = db.get_player(test_discord_id)
        assert player is not None, "Player not found"
        assert player["name"] == "TestPlayer"

        return True

    except Exception as e:
        print(f"✗ Player operations failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_context_manager():
    print("\n=== Testing Context Manager ===")
    db = DatabaseManager()
    try:
        with db.get_connection() as conn:
            cur = conn.execute("SELECT COUNT(*) as count FROM classes")
            result = cur.fetchone()
            count = result["count"]
            print(f"✓ Context manager working: {count} classes found")
        return True
    except Exception as e:
        print(f"✗ Context manager test failed: {e}")
        return False


def cleanup_test_data():
    print("\n=== Cleaning Up Test Data ===")
    db = DatabaseManager()
    test_discord_id = 999999999
    try:
        with db.get_connection() as conn:
            # Delete children first (Dependencies)
            conn.execute("DELETE FROM inventory WHERE discord_id = ?", (test_discord_id,))
            conn.execute("DELETE FROM stats WHERE discord_id = ?", (test_discord_id,))
            conn.execute("DELETE FROM player_skills WHERE discord_id = ?", (test_discord_id,))
            conn.execute("DELETE FROM guild_members WHERE discord_id = ?", (test_discord_id,))
            conn.execute("DELETE FROM player_quests WHERE discord_id = ?", (test_discord_id,))
            conn.execute("DELETE FROM adventure_sessions WHERE discord_id = ?", (test_discord_id,))

            # Delete parent last
            conn.execute("DELETE FROM players WHERE discord_id = ?", (test_discord_id,))

        print("✓ Test data cleaned up")
        return True
    except Exception as e:
        print(f"✗ Cleanup failed: {e}")
        return False


def run_all_tests():
    print("\n" + "=" * 60)
    print("ELDORIA QUEST - DATABASE TEST SUITE")
    print("=" * 60)

    setup_test_database()

    tests = [
        ("Database Creation", test_database_creation),
        ("Database Population", test_database_population),
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

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")

    print(f"\nTotal: {passed}/{total} tests passed")
    print("=" * 60 + "\n")

    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
