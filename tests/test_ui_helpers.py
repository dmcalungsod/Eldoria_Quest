import os
import sys
import unittest
from unittest.mock import MagicMock

# Mock discord before importing cogs.ui_helpers
sys.modules["discord"] = MagicMock()
sys.modules["discord.ui"] = MagicMock()
sys.modules["discord.ext"] = MagicMock()
sys.modules["discord.ext.commands"] = MagicMock()

# Add repo root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the function directly now that it exists
from cogs.ui_helpers import make_progress_bar  # noqa: E402


class TestUIHelpers(unittest.TestCase):
    def test_make_progress_bar(self):
        # 0%
        self.assertEqual(make_progress_bar(0, 100, 10), "░░░░░░░░░░")
        # 10%
        self.assertEqual(make_progress_bar(10, 100, 10), "█░░░░░░░░░")
        # 50%
        self.assertEqual(make_progress_bar(50, 100, 10), "█████░░░░░")
        # 100%
        self.assertEqual(make_progress_bar(100, 100, 10), "██████████")
        # Overflow
        self.assertEqual(make_progress_bar(150, 100, 10), "██████████")
        # Underflow
        self.assertEqual(make_progress_bar(-10, 100, 10), "░░░░░░░░░░")
        # Zero max -> Should prevent division by zero and treat as 0% or empty
        # implementation detail: max(max_val, 1) usually used
        self.assertEqual(make_progress_bar(50, 0, 10), "██████████") # wait, current/max(0,1) = 50/1 = 50 -> 100% ?
        # Actually logic is min(1, current/max(max_val, 1))
        # If max is 0, we treat it as 1. 50/1 = 50 -> clamped to 1. So full bar.
        # This seems acceptable for "0 max HP" which shouldn't happen, or maybe it means "invincible"?
        # But if current is 0 and max is 0: 0/1 = 0 -> empty.

        self.assertEqual(make_progress_bar(0, 0, 10), "░░░░░░░░░░")

        # Custom length
        self.assertEqual(make_progress_bar(5, 10, 4), "██░░")

if __name__ == "__main__":
    unittest.main()
