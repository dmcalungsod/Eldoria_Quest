import sys
import importlib
import unittest
from unittest.mock import MagicMock, patch

# Cleanup upstream test pollution so discord.py works correctly
for key in list(sys.modules.keys()):
    if key.startswith("discord"):
        if isinstance(sys.modules[key], MagicMock):
            del sys.modules[key]

# Mock pymongo globally
sys.modules["pymongo"] = MagicMock()
sys.modules["pymongo.errors"] = MagicMock()

import cogs.character_cog
importlib.reload(cogs.character_cog) # Ensure it loads with actual discord package

class TestCharacterCog(unittest.IsolatedAsyncioTestCase):
    @patch("cogs.character_cog.DatabaseManager")
    def setUp(self, mock_db_class):
        self.mock_bot = MagicMock()
        self.mock_db = mock_db_class.return_value

        self.cog = cogs.character_cog.CharacterCog(self.mock_bot)

    def test_init(self):
        """Test the initialization of the cog."""
        self.assertEqual(self.cog.bot, self.mock_bot)
        self.assertEqual(self.cog.db, self.mock_db)

if __name__ == "__main__":
    unittest.main()
