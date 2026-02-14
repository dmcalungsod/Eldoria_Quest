"""
Security Test Suite
-------------------
Verifies that player names are sanitized against Markdown injection and excessive length.
SAFE: Uses mocked DatabaseManager.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock

# Add root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.database_manager import DatabaseManager
from game_systems.player.player_creator import PlayerCreator


class TestSecurity(unittest.TestCase):
    def setUp(self):
        # Mock DatabaseManager
        self.mock_db = MagicMock(spec=DatabaseManager)
        self.creator = PlayerCreator(self.mock_db)

    def test_markdown_sanitization(self):
        """Test that markdown characters are removed from username."""
        discord_id = 12345
        dirty_name = "**Bold**_Italic_`Code`"
        expected_clean_name = "BoldItalicCode"

        # Mock player not existing
        self.mock_db.player_exists.return_value = False
        self.mock_db.get_default_skill_keys.return_value = []

        success, msg = self.creator.create_player(discord_id, dirty_name, 1) # 1 is a valid class_id

        self.assertTrue(success, f"Player creation failed: {msg}")

        # Verify create_player_full called with sanitized name
        self.mock_db.create_player_full.assert_called()
        args, kwargs = self.mock_db.create_player_full.call_args
        # username is 2nd positional arg or keyword 'username'
        actual_name = kwargs.get('username', args[1] if len(args) > 1 else None)

        self.assertEqual(actual_name, expected_clean_name, "Markdown characters were not removed!")

    def test_zalgo_and_length(self):
        """Test that name is truncated to 32 chars."""
        discord_id = 67890
        long_name = "A" * 50
        expected_len = 32

        self.mock_db.player_exists.return_value = False
        self.mock_db.get_default_skill_keys.return_value = []

        success, msg = self.creator.create_player(discord_id, long_name, 1)

        self.assertTrue(success, f"Player creation failed: {msg}")

        self.mock_db.create_player_full.assert_called()
        args, kwargs = self.mock_db.create_player_full.call_args
        actual_name = kwargs.get('username', args[1] if len(args) > 1 else None)

        self.assertEqual(len(actual_name), expected_len, "Name was not truncated!")
        self.assertEqual(actual_name, "A" * 32)

def run_all_tests():
    """Run the security test suite manually."""
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestSecurity)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()

if __name__ == '__main__':
    unittest.main()
