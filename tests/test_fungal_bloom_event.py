import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock pymongo BEFORE importing DatabaseManager
mock_pymongo = MagicMock()
sys.modules["pymongo"] = mock_pymongo
sys.modules["pymongo.errors"] = MagicMock()

from game_systems.adventure.adventure_rewards import AdventureRewards  # noqa: E402
from game_systems.adventure.adventure_session import AdventureSession  # noqa: E402
from game_systems.events.world_event_system import WorldEventSystem  # noqa: E402
from game_systems.player.player_stats import PlayerStats  # noqa: E402


class TestFungalBloomEvent(unittest.TestCase):
    def setUp(self):
        self.db_mock = MagicMock()
        self.quest_system_mock = MagicMock()
        self.inventory_manager_mock = MagicMock()
        self.discord_id = 12345

        self.session = AdventureSession(
            db=self.db_mock,
            quest_system=self.quest_system_mock,
            inventory_manager=self.inventory_manager_mock,
            discord_id=self.discord_id,
        )

        self.rewards = AdventureRewards(db=self.db_mock, discord_id=self.discord_id)

    @patch("game_systems.adventure.adventure_session.LOCATIONS")
    def test_threat_reduction_in_undergrove(self, mock_locations):
        """Test that the threat reduction multiplier is applied during the event in The Undergrove."""
        # Setup location
        mock_locations.get.return_value = {"name": "The Undergrove"}
        self.session.location_id = "the_undergrove"
        self.session.active_monster = None

        # Setup context with the event active
        context = {
            "player_stats": MagicMock(spec=PlayerStats),
            "vitals": {"current_hp": 100, "current_mp": 50},
            "player_row": {"level": 10},
            "active_boosts": {
                "undergrove_threat_reduction": 0.8,
            },
            "event_type": WorldEventSystem.FUNGAL_BLOOM,
        }

        # Directly test the helper method instead of full simulate_step since that is how it's factored
        passed_threat_reduction = self.session._calculate_threat_reduction(context)

        self.assertEqual(passed_threat_reduction, 0.8, "Threat reduction was not applied correctly in The Undergrove.")

    @patch("game_systems.adventure.adventure_session.LOCATIONS")
    def test_threat_reduction_not_applied_elsewhere(self, mock_locations):
        """Test that the threat reduction is NOT applied outside The Undergrove."""
        mock_locations.get.return_value = {"name": "Some Other Place"}
        self.session.location_id = "some_other_place"
        self.session.active_monster = {"name": "Test Monster"}

        context = {
            "player_stats": MagicMock(spec=PlayerStats),
            "vitals": {"current_hp": 100, "current_mp": 50},
            "player_row": {"level": 10},
            "active_boosts": {
                "undergrove_threat_reduction": 0.8,
            },
            "event_type": WorldEventSystem.FUNGAL_BLOOM,
        }
        passed_threat_reduction = self.session._calculate_threat_reduction(context)

        self.assertEqual(
            passed_threat_reduction, 1.0, "Threat reduction was incorrectly applied outside The Undergrove."
        )

    @patch("game_systems.adventure.adventure_rewards.LootCalculator.roll_drops")
    def test_loot_bonus_in_undergrove(self, mock_roll_drops):
        """Test that the 100% loot bonus is passed to the LootCalculator in The Undergrove."""
        mock_roll_drops.return_value = ["test_item"]
        self.db_mock.get_player_stats_json.return_value = {"LUCK": {"base": 10}}
        self.db_mock.get_active_world_event.return_value = {"type": WorldEventSystem.FUNGAL_BLOOM}

        combat_result = {
            "exp": 100,
            "aurum": 50,
            "monster_data": {"name": "Test Boss", "tier": "Boss"},
            "drops": ["test_item"],
            "active_boosts": {
                "loot_boost": 1.25,  # Base global event boost
                "undergrove_loot_bonus": 2.0,
            },
        }

        self.rewards._process_loot_and_quests(
            combat_result=combat_result,
            quest_system=self.quest_system_mock,
            inventory_manager=self.inventory_manager_mock,
            session_loot={},
            logs=[],
            location_id="the_undergrove",
        )

        mock_roll_drops.assert_called_once()
        args, kwargs = mock_roll_drops.call_args
        # roll_drops signature: drops_list, luck, loot_boost
        passed_loot_boost = args[2]

        # Expected: 1.25 (global) * 2.0 (local Undergrove) = 2.5
        self.assertAlmostEqual(
            passed_loot_boost, 2.5, places=3, msg="Loot boost was not calculated correctly in The Undergrove."
        )

    @patch("game_systems.adventure.adventure_rewards.LootCalculator.roll_drops")
    def test_loot_bonus_not_applied_elsewhere(self, mock_roll_drops):
        """Test that the Undergrove loot bonus is NOT applied elsewhere."""
        mock_roll_drops.return_value = ["test_item"]
        self.db_mock.get_player_stats_json.return_value = {"LUCK": {"base": 10}}
        self.db_mock.get_active_world_event.return_value = {"type": WorldEventSystem.FUNGAL_BLOOM}

        combat_result = {
            "exp": 100,
            "aurum": 50,
            "monster_data": {"name": "Test Boss", "tier": "Boss"},
            "drops": ["test_item"],
            "active_boosts": {
                "loot_boost": 1.25,  # Base global event boost
                "undergrove_loot_bonus": 2.0,
            },
        }

        self.rewards._process_loot_and_quests(
            combat_result=combat_result,
            quest_system=self.quest_system_mock,
            inventory_manager=self.inventory_manager_mock,
            session_loot={},
            logs=[],
            location_id="some_other_place",
        )

        args, kwargs = mock_roll_drops.call_args
        passed_loot_boost = args[2]

        # Expected: 1.25 (global only)
        self.assertAlmostEqual(
            passed_loot_boost, 1.25, places=3, msg="Loot boost was incorrectly calculated outside The Undergrove."
        )


if __name__ == "__main__":
    unittest.main()
