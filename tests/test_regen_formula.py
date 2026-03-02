import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add repo root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock pymongo
mock_pymongo = MagicMock()
sys.modules["pymongo"] = mock_pymongo
sys.modules["pymongo.errors"] = mock_pymongo.errors

from game_systems.adventure.event_handler import EventHandler  # noqa: E402
from game_systems.player.player_stats import PlayerStats  # noqa: E402


class TestRegenFormula(unittest.TestCase):
    def setUp(self):
        self.db = MagicMock()
        self.quest_system = MagicMock()
        self.event_handler = EventHandler(self.db, self.quest_system, 12345)

    @patch("game_systems.adventure.event_handler.AdventureEvents")
    @patch("game_systems.adventure.event_handler.WorldTime")
    def test_regeneration_scaling(self, mock_world_time, mock_events):
        mock_world_time.get_current_phase.return_value = "Day"
        mock_events.regeneration.return_value = ["Resting..."]

        # Helper to run regen
        def run_regen(endurance):
            stats = PlayerStats(end_base=endurance, mag_base=10)
            max_hp = stats.max_hp

            context = {
                "player_stats": stats,
                "vitals": {"current_hp": 1, "current_mp": 1},
                "player_row": {"class_id": 1},
            }

            self.event_handler._perform_regeneration(context)

            # Extract regen amount from context update
            # The context is updated in place
            new_hp = context["vitals"]["current_hp"]
            regen_amount = new_hp - 1
            return regen_amount, max_hp

        # Case 1: Low Endurance (10)
        # Old Formula: 10 * 0.5 + 1 = 6.
        # New Formula: 10 * 0.25 + 1 = 2.5 -> 2 + 1 = 3.
        regen_10, _max_hp_10 = run_regen(10)
        self.assertEqual(regen_10, 3, "Low Endurance regen incorrect")

        # Case 2: Mid Endurance (100)
        # Old Formula: 100 * 0.5 + 1 = 51.
        # New Formula: 100 * 0.25 + 1 = 26.
        # Cap 5% of 1050 = 52. Cap 10% = 105.
        # So it should be 26 (limited by base).
        regen_100, _max_hp_100 = run_regen(100)
        self.assertEqual(regen_100, 26, "Mid Endurance regen incorrect")

        # Case 3: High Endurance (1000)
        # Old Formula: 1000 * 0.5 + 1 = 501.
        # New Formula: 1000 * 0.25 + 1 = 251.
        # MaxHP ~ 21300.
        # Cap 5% = 1065. Cap 10% = 2130.
        # So it should be 251 (limited by base).
        regen_1000, _max_hp_1000 = run_regen(1000)
        self.assertEqual(regen_1000, 251, "High Endurance regen incorrect")


if __name__ == "__main__":
    unittest.main()
