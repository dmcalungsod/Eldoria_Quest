import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from unittest.mock import MagicMock  # noqa: E402

# Mock pymongo
sys.modules["pymongo"] = MagicMock()
sys.modules["pymongo.errors"] = MagicMock()

from database.database_manager import DatabaseManager  # noqa: E402


class TestInfirmaryLogic(unittest.TestCase):
    def test_calculate_heal_cost_zero_missing(self):
        # Full health
        cost = DatabaseManager.calculate_heal_cost(current_hp=100, current_mp=50, max_hp=100, max_mp=50)
        self.assertEqual(cost, 0)

    def test_calculate_heal_cost_negative_missing(self):
        # Overhealed (should treat as 0 cost)
        cost = DatabaseManager.calculate_heal_cost(current_hp=110, current_mp=60, max_hp=100, max_mp=50)
        self.assertEqual(cost, 0)

    def test_calculate_heal_cost_hp_only(self):
        # Missing 10 HP (Rate 2.0) -> 20 Aurum
        cost = DatabaseManager.calculate_heal_cost(current_hp=90, current_mp=50, max_hp=100, max_mp=50)
        self.assertEqual(cost, 20)

    def test_calculate_heal_cost_mp_only(self):
        # Missing 10 MP (Rate 3.0) -> 30 Aurum
        cost = DatabaseManager.calculate_heal_cost(current_hp=100, current_mp=40, max_hp=100, max_mp=50)
        self.assertEqual(cost, 30)

    def test_calculate_heal_cost_mixed(self):
        # Missing 10 HP (20) + 10 MP (30) -> 50 Aurum
        cost = DatabaseManager.calculate_heal_cost(current_hp=90, current_mp=40, max_hp=100, max_mp=50)
        self.assertEqual(cost, 50)

    def test_calculate_heal_cost_minimum_nonzero(self):
        # Even 1 HP missing costs 2 Aurum.
        # Even 1 MP missing costs 3 Aurum.
        # The formula has max(1, ...), so result is never 0 if missing > 0.
        cost = DatabaseManager.calculate_heal_cost(current_hp=99, current_mp=50, max_hp=100, max_mp=50)
        self.assertEqual(cost, 2)


if __name__ == "__main__":
    unittest.main()
