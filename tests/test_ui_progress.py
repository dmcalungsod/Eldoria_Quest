import os
import sys
import unittest
from unittest.mock import MagicMock

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# --- MOCKING DEPENDENCIES ---
# We must mock everything that cogs.ui_helpers imports to avoid runtime errors
# in this standalone test environment where dependencies might be missing.

sys.modules["discord"] = MagicMock()
sys.modules["discord.ext"] = MagicMock()
sys.modules["discord.ext.commands"] = MagicMock()

sys.modules["database"] = MagicMock()
sys.modules["database.database_manager"] = MagicMock()

sys.modules["game_systems"] = MagicMock()
sys.modules["game_systems.data"] = MagicMock()
sys.modules["game_systems.data.emojis"] = MagicMock()
sys.modules["game_systems.player"] = MagicMock()
sys.modules["game_systems.player.player_stats"] = MagicMock()
sys.modules["game_systems.character"] = MagicMock()
sys.modules["game_systems.character.ui"] = MagicMock()
sys.modules["game_systems.character.ui.profile_view"] = MagicMock()


class TestProgressBar(unittest.TestCase):
    def test_import(self):
        """Verify we can import make_progress_bar from cogs.ui_helpers."""
        try:
            from cogs.ui_helpers import make_progress_bar  # noqa: E402
            self.assertTrue(callable(make_progress_bar))
        except ImportError:
            self.fail("make_progress_bar could not be imported from cogs.ui_helpers")

    def test_standard_values(self):
        from cogs.ui_helpers import make_progress_bar  # noqa: E402

        # 50% of 10 -> 5 blocks
        self.assertEqual(make_progress_bar(50, 100, 10), "█████░░░░░")

        # 10% of 10 -> 1 block
        self.assertEqual(make_progress_bar(10, 100, 10), "█░░░░░░░░░")

        # 100% -> 10 blocks
        self.assertEqual(make_progress_bar(100, 100, 10), "██████████")

        # 0% -> 0 blocks
        self.assertEqual(make_progress_bar(0, 100, 10), "░░░░░░░░░░")

    def test_edge_cases(self):
        from cogs.ui_helpers import make_progress_bar  # noqa: E402

        # Negative current -> 0%
        self.assertEqual(make_progress_bar(-10, 100, 10), "░░░░░░░░░░")

        # Current > Max -> 100%
        self.assertEqual(make_progress_bar(150, 100, 10), "██████████")

        # Max is 0 -> Should avoid division by zero and treat as full or empty?
        # Logic says: if max <= 0, max=1. So 50/1 = 50 -> >100% -> Full
        self.assertEqual(make_progress_bar(50, 0, 10), "██████████")

        # Max is 0, Current is 0 -> 0/1 = 0%
        self.assertEqual(make_progress_bar(0, 0, 10), "░░░░░░░░░░")

    def test_custom_length(self):
        from cogs.ui_helpers import make_progress_bar  # noqa: E402

        # 50% of 20 -> 10 blocks
        bar = make_progress_bar(50, 100, 20)
        self.assertEqual(len(bar), 20)
        self.assertEqual(bar.count("█"), 10)
        self.assertEqual(bar.count("░"), 10)

if __name__ == "__main__":
    unittest.main()
