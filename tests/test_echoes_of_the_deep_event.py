import unittest
from unittest.mock import MagicMock, patch

from game_systems.adventure.adventure_rewards import AdventureRewards
from game_systems.adventure.adventure_session import AdventureSession
from game_systems.events.world_event_system import WorldEventSystem
from game_systems.player.player_stats import PlayerStats


class TestEchoesOfTheDeepEvent(unittest.TestCase):
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
    def test_threat_reduction_in_wailing_chasm(self, mock_locations):
        """Test that the threat reduction multiplier is applied during the event in the Wailing Chasm."""
        # Setup location
        mock_locations.get.return_value = {"name": "The Wailing Chasm"}
        self.session.location_id = "the_wailing_chasm"
        self.session.active_monster = None

        # Setup context with the event active
        context = {
            "player_stats": MagicMock(spec=PlayerStats),
            "vitals": {"current_hp": 100, "current_mp": 50},
            "player_row": {"level": 10},
            "active_boosts": {
                "wailing_chasm_threat_reduction": 0.9,
            },
            "event_type": WorldEventSystem.ECHOES_OF_THE_DEEP,
        }

        # Mock the context fetcher so we can directly pass our context
        self.session._fetch_session_context = MagicMock(return_value=context)
        # Prevent actual combat/encounters from happening
        self.session._handle_new_encounter = MagicMock(return_value=None)
        self.session._handle_exploration_event = MagicMock(return_value={"log": ["Test"]})

        # We can mock calculate_fatigue_multiplier to see if threat reduction is applied,
        # but in simulate_step, threat_reduction is passed to _resolve_auto_combat or _process_combat_turn.
        # Let's mock _handle_active_combat to capture what is passed to it.
        self.session.active_monster = {"name": "Test Monster"}
        self.session._handle_active_combat = MagicMock()

        self.session.simulate_step(context_bundle=context)

        # _handle_active_combat signature: context, action, background, persist, weather, time_phase, threat_reduction
        self.session._handle_active_combat.assert_called_once()
        args, kwargs = self.session._handle_active_combat.call_args
        # threat_reduction is the 7th argument
        passed_threat_reduction = args[6]

        self.assertEqual(passed_threat_reduction, 0.9, "Threat reduction was not applied correctly in Wailing Chasm.")

    @patch("game_systems.adventure.adventure_session.LOCATIONS")
    def test_threat_reduction_not_applied_elsewhere(self, mock_locations):
        """Test that the threat reduction is NOT applied outside the Wailing Chasm."""
        mock_locations.get.return_value = {"name": "Some Other Place"}
        self.session.location_id = "some_other_place"
        self.session.active_monster = {"name": "Test Monster"}

        context = {
            "player_stats": MagicMock(spec=PlayerStats),
            "vitals": {"current_hp": 100, "current_mp": 50},
            "player_row": {"level": 10},
            "active_boosts": {
                "wailing_chasm_threat_reduction": 0.9,
            },
            "event_type": WorldEventSystem.ECHOES_OF_THE_DEEP,
        }
        self.session._fetch_session_context = MagicMock(return_value=context)
        self.session._handle_active_combat = MagicMock()

        self.session.simulate_step(context_bundle=context)

        args, kwargs = self.session._handle_active_combat.call_args
        passed_threat_reduction = args[6]

        self.assertEqual(
            passed_threat_reduction, 1.0, "Threat reduction was incorrectly applied outside Wailing Chasm."
        )

    @patch("game_systems.adventure.adventure_rewards.LootCalculator")
    def test_loot_bonus_in_wailing_chasm(self, mock_loot_calc):
        """Test that the 50% loot bonus is passed to the LootCalculator in the Wailing Chasm."""
        mock_loot_calc.roll_drops.return_value = ["test_item"]
        self.db_mock.get_player_stats_json.return_value = {"LUCK": {"base": 10}}
        self.db_mock.get_active_world_event.return_value = {"type": WorldEventSystem.ECHOES_OF_THE_DEEP}

        combat_result = {
            "exp": 100,
            "aurum": 50,
            "monster_data": {"name": "Test Boss", "tier": "Boss"},
            "drops": ["test_item"],
            "active_boosts": {
                "loot_boost": 1.25,  # Base global event boost
                "wailing_chasm_loot_bonus": 1.5,
            },
        }

        self.rewards._process_loot_and_quests(
            combat_result=combat_result,
            quest_system=self.quest_system_mock,
            inventory_manager=self.inventory_manager_mock,
            session_loot={},
            logs=[],
            location_id="the_wailing_chasm",
        )

        mock_loot_calc.roll_drops.assert_called_once()
        args, kwargs = mock_loot_calc.roll_drops.call_args
        # roll_drops signature: drops_list, luck, loot_boost
        passed_loot_boost = args[2]

        # Expected: 1.25 (global) * 1.5 (local Wailing Chasm) = 1.875
        self.assertAlmostEqual(
            passed_loot_boost, 1.875, places=3, msg="Loot boost was not calculated correctly in Wailing Chasm."
        )

    @patch("game_systems.adventure.adventure_rewards.LootCalculator")
    def test_loot_bonus_not_applied_elsewhere(self, mock_loot_calc):
        """Test that the Wailing Chasm loot bonus is NOT applied elsewhere."""
        mock_loot_calc.roll_drops.return_value = ["test_item"]
        self.db_mock.get_player_stats_json.return_value = {"LUCK": {"base": 10}}
        self.db_mock.get_active_world_event.return_value = {"type": WorldEventSystem.ECHOES_OF_THE_DEEP}

        combat_result = {
            "exp": 100,
            "aurum": 50,
            "monster_data": {"name": "Test Boss", "tier": "Boss"},
            "drops": ["test_item"],
            "active_boosts": {
                "loot_boost": 1.25,  # Base global event boost
                "wailing_chasm_loot_bonus": 1.5,
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

        args, kwargs = mock_loot_calc.roll_drops.call_args
        passed_loot_boost = args[2]

        # Expected: 1.25 (global only)
        self.assertAlmostEqual(
            passed_loot_boost, 1.25, places=3, msg="Loot boost was incorrectly calculated outside Wailing Chasm."
        )


if __name__ == "__main__":
    unittest.main()
