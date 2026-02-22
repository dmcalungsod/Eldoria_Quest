
import math
import sys
import unittest
from unittest.mock import MagicMock

# Mock discord and related modules BEFORE importing the cog
mock_discord = MagicMock()
sys.modules["discord"] = mock_discord
sys.modules["discord.ext"] = MagicMock()
sys.modules["discord.ext.commands"] = MagicMock()

# Mock pymongo and its submodules
sys.modules["pymongo"] = MagicMock()
sys.modules["pymongo.errors"] = MagicMock()
sys.modules["pymongo.collection"] = MagicMock()
sys.modules["pymongo.results"] = MagicMock()
# Also mock database.database_manager if needed, but we want to import it for StatusUpdateView to work
# However, StatusUpdateView imports DatabaseManager. Let's let it import, but with mocked pymongo it should be fine.

# Mock discord.ui.View
class MockView:
    def __init__(self, timeout=None):
        pass

    def add_item(self, item):
        pass

mock_ui = MagicMock()
mock_ui.View = MockView
mock_ui.Button = MagicMock()
sys.modules["discord.ui"] = mock_ui
mock_discord.ui = mock_ui

# Mock DatabaseManager and PlayerStats if needed, but we can mock them in the test method
# However, the cog imports PlayerStats at module level.
# We can let it import the real PlayerStats if it doesn't cause issues, or mock it.
# game_systems.player.player_stats imports nothing heavy.
# game_systems.data.class_data imports nothing heavy.
# So we can probably import the cog now.

# We need to make sure we can import cogs.status_update_cog
# We might need to add repo root to sys.path if not already there, but tests usually run from root.
# Just in case:
import os
sys.path.insert(0, os.getcwd())

try:
    from cogs.status_update_cog import StatusUpdateView, BASE_STAT_COSTS # noqa: E402
except ImportError:
    # If import fails, we might be running from inside tests/
    sys.path.insert(0, os.path.dirname(os.getcwd()))
    from cogs.status_update_cog import StatusUpdateView, BASE_STAT_COSTS # noqa: E402


class TestVPCostCurve(unittest.TestCase):
    def setUp(self):
        self.mock_db = MagicMock()
        self.mock_user = MagicMock()
        self.mock_p_data = {"class_id": "warrior", "vestige_pool": 1000}
        self.mock_stats = MagicMock()
        self.mock_stats_row = {}

        # Instantiate view with mocks
        # We need to mock _get_class_starting_stats to return known values
        # But _get_class_starting_stats reads from CLASSES.
        # We can either mock CLASSES or just let it run if CLASSES is available.
        # Or we can patch _get_class_starting_stats on the instance.
        pass

    def test_cost_curve_exponential(self):
        # Mock get_base_stats_dict to return integers BEFORE instantiation
        self.mock_stats.get_base_stats_dict.return_value = {"STR": 1, "END": 1, "DEX": 1, "AGI": 1, "MAG": 1, "LCK": 1}

        # Create instance
        view = StatusUpdateView(
            self.mock_db,
            self.mock_user,
            self.mock_p_data,
            self.mock_stats,
            self.mock_stats_row
        )

        # Override starting stats for deterministic testing
        # Assume all stats start at 1 for simplicity, unless specified
        view.starting_stats = {"STR": 1, "END": 1, "DEX": 1, "AGI": 1, "MAG": 1, "LCK": 1}

        # Test Case 1: STR (Base Cost 10)
        stat = "STR"
        base_cost = 10
        exponent = 1.5

        # Helper to calculate expected cost
        def expected_cost(invested):
            return math.floor(base_cost * ((invested + 1) ** exponent))

        # Test various investment levels
        # current_val = starting_stat + invested

        # Invested 0 (Current 1) -> Cost for point 1 (going to 2)
        # Wait, if I have 1 STR (start), invested is 0.
        # Cost to buy next point (to 2) should be based on invested=0?
        # "Point 1: floor(10 * 1^1.5) = 10".
        # If this is the FIRST point you buy, then invested is 0?
        # Yes.
        self.assertEqual(view._calculate_single_point_cost(stat, 1), expected_cost(0), "Cost for 1st point (invested 0) mismatch")

        # Invested 1 (Current 2) -> Cost for point 2
        self.assertEqual(view._calculate_single_point_cost(stat, 2), expected_cost(1), "Cost for 2nd point (invested 1) mismatch")

        # Invested 9 (Current 10) -> Cost for point 10
        self.assertEqual(view._calculate_single_point_cost(stat, 10), expected_cost(9), "Cost for 10th point (invested 9) mismatch")

        # Invested 49 (Current 50) -> Cost for point 50
        self.assertEqual(view._calculate_single_point_cost(stat, 50), expected_cost(49), "Cost for 50th point (invested 49) mismatch")

        # Invested 99 (Current 100) -> Cost for point 100
        self.assertEqual(view._calculate_single_point_cost(stat, 100), expected_cost(99), "Cost for 100th point (invested 99) mismatch")

    def test_luck_cost_curve(self):
        # LCK has base cost 20
        self.mock_stats.get_base_stats_dict.return_value = {"STR": 1, "END": 1, "DEX": 1, "AGI": 1, "MAG": 1, "LCK": 1}

        view = StatusUpdateView(
            self.mock_db,
            self.mock_user,
            self.mock_p_data,
            self.mock_stats,
            self.mock_stats_row
        )
        view.starting_stats = {"LCK": 1}

        stat = "LCK"
        base_cost = 20
        exponent = 1.5

        def expected_cost(invested):
            return math.floor(base_cost * ((invested + 1) ** exponent))

        self.assertEqual(view._calculate_single_point_cost(stat, 1), expected_cost(0))
        self.assertEqual(view._calculate_single_point_cost(stat, 10), expected_cost(9))

if __name__ == "__main__":
    unittest.main()
