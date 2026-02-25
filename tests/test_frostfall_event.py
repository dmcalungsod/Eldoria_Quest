import datetime
import sys
import unittest
from unittest.mock import MagicMock, patch

# Mock modules before importing
sys.modules["pymongo"] = MagicMock()
sys.modules["pymongo.errors"] = MagicMock()
sys.modules["discord"] = MagicMock()

from game_systems.adventure.adventure_rewards import AdventureRewards  # noqa: E402
from game_systems.adventure.adventure_session import AdventureSession  # noqa: E402
from game_systems.events.world_event_system import WorldEventSystem  # noqa: E402


class TestFrostfallEvent(unittest.TestCase):
    def setUp(self):
        self.mock_db = MagicMock()
        self.system = WorldEventSystem(self.mock_db)

        # Patch WorldTime
        self.patcher = patch("game_systems.events.world_event_system.WorldTime")
        self.mock_world_time = self.patcher.start()
        self.mock_world_time.now.side_effect = datetime.datetime.now

        # Patch AdventureSession dependencies
        self.mock_quest = MagicMock()
        self.mock_inv = MagicMock()

    def tearDown(self):
        self.patcher.stop()

    def test_start_frostfall_event(self):
        """Verify we can start the event and it has correct modifiers."""
        success = self.system.start_event(WorldEventSystem.FROSTFALL_EXPEDITION, 24)
        self.assertTrue(success)
        self.mock_db.set_active_world_event.assert_called_with(
            WorldEventSystem.FROSTFALL_EXPEDITION, unittest.mock.ANY, unittest.mock.ANY
        )

        # Mock DB returning the event
        self.mock_db.get_active_world_event.return_value = {
            "type": WorldEventSystem.FROSTFALL_EXPEDITION,
            "end_time": "2099-01-01T00:00:00",
            "active": 1,
        }

        event = self.system.get_current_event()
        self.assertEqual(event["name"], "The Frostfall Expedition")
        self.assertEqual(event["modifiers"]["frostfall_threat_reduction"], 0.9)
        self.assertEqual(event["modifiers"]["frostfall_loot_bonus"], 1.5)

    @patch("game_systems.adventure.adventure_session.AdventureRewards")
    @patch("game_systems.adventure.adventure_session.CombatHandler")
    @patch("game_systems.adventure.adventure_session.EventHandler")
    def test_adventure_session_threat_reduction(self, mock_event, mock_combat, mock_rewards):
        """Verify AdventureSession applies threat reduction in Frostfall."""
        discord_id = 123
        session = AdventureSession(self.mock_db, self.mock_quest, self.mock_inv, discord_id)
        session.location_id = "frostfall_expanse"
        session.active_monster = {"name": "Test Monster"}  # Active monster needed for combat

        # Mock Context Bundle
        bundle = {
            "stats": {"HP": 100, "MP": 100},
            "buffs": [],
            "player": {"current_hp": 100, "current_mp": 100},
            "skills": [],
        }
        self.mock_db.get_combat_context_bundle.return_value = bundle

        # Mock Active Boosts (Event is active)
        self.mock_db.get_active_boosts.return_value = []
        # We need WorldEventSystem to return the event inside _fetch_session_context
        # So we patch AdventureSession's WorldEventSystem usage or mock DB call
        self.mock_db.get_active_world_event.return_value = {
            "type": WorldEventSystem.FROSTFALL_EXPEDITION,
            "end_time": "2099-01-01T00:00:00",
            "active": 1,
        }

        # Mock Combat Handler
        mock_combat_instance = mock_combat.return_value
        mock_combat_instance.resolve_turn.return_value = {
            "winner": "player",
            "hp_current": 100,
            "mp_current": 100,
            "monster_hp": 0,
            "turn_report": {},
            "monster_data": {"name": "Test"},
            "phrases": ["Combat happens"],
        }

        # Mock Rewards
        mock_rewards_instance = mock_rewards.return_value
        mock_rewards_instance.process_victory.return_value = []

        # Run Simulate Step
        session.simulate_step(action="attack")

        # Verify resolve_turn called with reduced fatigue multiplier
        # 1.0 (base) * 0.9 (threat reduction) = 0.9
        args, kwargs = mock_combat_instance.resolve_turn.call_args
        self.assertAlmostEqual(kwargs["fatigue_multiplier"], 0.9)

    @patch("game_systems.adventure.adventure_session.AdventureRewards")
    @patch("game_systems.adventure.adventure_session.CombatHandler")
    @patch("game_systems.adventure.adventure_session.EventHandler")
    def test_adventure_session_no_threat_reduction_elsewhere(self, mock_event, mock_combat, mock_rewards):
        """Verify AdventureSession DOES NOT apply threat reduction elsewhere."""
        discord_id = 123
        session = AdventureSession(self.mock_db, self.mock_quest, self.mock_inv, discord_id)
        session.location_id = "forest_outskirts"  # NOT Frostfall
        session.active_monster = {"name": "Test Monster"}

        bundle = {
            "stats": {"HP": 100, "MP": 100},
            "buffs": [],
            "player": {"current_hp": 100, "current_mp": 100},
            "skills": [],
        }
        self.mock_db.get_combat_context_bundle.return_value = bundle

        self.mock_db.get_active_boosts.return_value = []
        self.mock_db.get_active_world_event.return_value = {
            "type": WorldEventSystem.FROSTFALL_EXPEDITION,
            "end_time": "2099-01-01T00:00:00",
            "active": 1,
        }

        mock_combat_instance = mock_combat.return_value
        mock_combat_instance.resolve_turn.return_value = {
            "winner": "player",
            "hp_current": 100,
            "mp_current": 100,
            "monster_hp": 0,
            "turn_report": {},
            "monster_data": {"name": "Test"},
            "phrases": ["Combat happens"],
        }

        mock_rewards_instance = mock_rewards.return_value
        mock_rewards_instance.process_victory.return_value = []

        session.simulate_step(action="attack")

        # Verify resolve_turn called with NORMAL multiplier (1.0)
        args, kwargs = mock_combat_instance.resolve_turn.call_args
        self.assertAlmostEqual(kwargs["fatigue_multiplier"], 1.0)

    @patch("game_systems.adventure.adventure_rewards.LootCalculator")
    def test_adventure_rewards_loot_bonus(self, mock_loot_calc):
        """Verify AdventureRewards applies loot bonus in Frostfall."""
        rewards = AdventureRewards(self.mock_db, 123)

        # Setup Inputs
        combat_result = {
            "exp": 100,
            "drops": ["item1"],
            "monster_data": {"name": "Test", "tier": "Normal"},
            "active_boosts": {
                "loot_boost": 1.25,  # Base event boost
                "frostfall_loot_bonus": 1.5,  # Specific bonus
            },
        }

        self.mock_db.get_player_stats_json.return_value = {"luck": 10}
        self.mock_db.get_player_quests.return_value = []

        # Call process_victory with location
        rewards.process_victory(
            battle_report={},
            report_list=[],
            combat_result=combat_result,
            quest_system=self.mock_quest,
            inventory_manager=self.mock_inv,
            session_loot={},
            location_id="frostfall_expanse",
        )

        # Verify LootCalculator called with combined boost
        # 1.25 * 1.5 = 1.875
        args, kwargs = mock_loot_calc.roll_drops.call_args
        # args[2] is loot_boost
        self.assertAlmostEqual(args[2], 1.875)

    @patch("game_systems.adventure.adventure_rewards.LootCalculator")
    def test_adventure_rewards_no_bonus_elsewhere(self, mock_loot_calc):
        """Verify AdventureRewards DOES NOT apply bonus elsewhere."""
        rewards = AdventureRewards(self.mock_db, 123)

        combat_result = {
            "exp": 100,
            "drops": ["item1"],
            "monster_data": {"name": "Test", "tier": "Normal"},
            "active_boosts": {"loot_boost": 1.25, "frostfall_loot_bonus": 1.5},
        }

        self.mock_db.get_player_stats_json.return_value = {"luck": 10}
        self.mock_db.get_player_quests.return_value = []

        rewards.process_victory(
            battle_report={},
            report_list=[],
            combat_result=combat_result,
            quest_system=self.mock_quest,
            inventory_manager=self.mock_inv,
            session_loot={},
            location_id="forest_outskirts",  # NOT Frostfall
        )

        # Verify LootCalculator called with base boost only (1.25)
        args, kwargs = mock_loot_calc.roll_drops.call_args
        self.assertAlmostEqual(args[2], 1.25)


if __name__ == "__main__":
    unittest.main()
