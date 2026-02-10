"""
Security Test Suite
-------------------
Verifies that player names are sanitized against Markdown injection and excessive length.
"""

import os
import sys
import tempfile
import unittest

# Add root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import importlib
import database.database_manager as db_manager_module
from database.database_manager import DatabaseManager
import database.create_database as db_create
import database.populate_database as db_populate
from game_systems.player.player_creator import PlayerCreator

class TestSecurity(unittest.TestCase):
    def setUp(self):
        # FORCE CLEAN STATE: Reload module to clear any patches
        importlib.reload(db_manager_module)
        # Re-import DatabaseManager from the reloaded module
        global DatabaseManager
        from database.database_manager import DatabaseManager

        # Create temp DB
        self.db_fd, self.db_path = tempfile.mkstemp()

        # Patch DatabaseManager to use temp DB
        self.original_db_name = db_manager_module.DATABASE_NAME
        db_manager_module.DATABASE_NAME = self.db_path
        db_create.DATABASE_NAME = self.db_path
        db_populate.DATABASE_NAME = self.db_path

        # Init DB
        db_create.create_tables()
        db_populate.main()

        # Reset Singleton if it exists
        DatabaseManager._instance = None
        DatabaseManager._initialized = False

        self.db = DatabaseManager(self.db_path)
        self.creator = PlayerCreator(self.db)

    def tearDown(self):
        # Reset Singleton
        DatabaseManager._instance = None
        DatabaseManager._initialized = False

        # Remove temp file
        os.close(self.db_fd)
        os.remove(self.db_path)

        # Restore DB name
        db_manager_module.DATABASE_NAME = self.original_db_name

    def test_markdown_sanitization(self):
        """Test that markdown characters are removed from username."""
        discord_id = 12345
        dirty_name = "**Bold**_Italic_`Code`"
        expected_clean_name = "BoldItalicCode"

        success, msg = self.creator.create_player(discord_id, dirty_name, 1) # 1 is a valid class_id

        self.assertTrue(success, f"Player creation failed: {msg}")

        player = self.db.get_player(discord_id)
        self.assertIsNotNone(player)
        self.assertEqual(player['name'], expected_clean_name, "Markdown characters were not removed!")

    def test_zalgo_and_length(self):
        """Test that name is truncated to 32 chars and weird chars handled."""
        discord_id = 67890
        long_name = "A" * 50
        expected_len = 32

        success, msg = self.creator.create_player(discord_id, long_name, 1)

        self.assertTrue(success, f"Player creation failed: {msg}")

        player = self.db.get_player(discord_id)
        self.assertEqual(len(player['name']), expected_len, "Name was not truncated!")
        self.assertEqual(player['name'], "A" * 32)

def run_all_tests():
    """Run the security test suite manually."""
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestSecurity)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()

if __name__ == '__main__':
    run_all_tests()
