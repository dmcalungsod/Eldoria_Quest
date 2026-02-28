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


class TestExpeditionDriveEvent(unittest.TestCase):
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

    def test_start_expedition_drive_event(self):
        """Verify we can start the event and it has correct modifiers."""
        success = self.system.start_event(WorldEventSystem.GUILD_EXPEDITION_DRIVE, 48)
        self.assertTrue(success)
        self.mock_db.set_active_world_event.assert_called_with(
            WorldEventSystem.GUILD_EXPEDITION_DRIVE, unittest.mock.ANY, unittest.mock.ANY
        )

        # Mock DB returning the event
        self.mock_db.get_active_world_event.return_value = {
            "type": WorldEventSystem.GUILD_EXPEDITION_DRIVE,
            "end_time": "2099-01-01T00:00:00",
            "active": 1,
        }

        event = self.system.get_current_event()
        self.assertEqual(event["name"], "Guild Expedition Drive")
        self.assertEqual(event["modifiers"]["fatigue_reduction"], 0.8)
        self.assertEqual(event["modifiers"]["exp_boost"], 1.25)
        self.assertEqual(event["modifiers"]["loot_boost"], 1.25)

    @patch("game_systems.adventure.adventure_session.AdventureRewards")
    @patch("game_systems.adventure.adventure_session.CombatHandler")
    @patch("game_systems.adventure.adventure_session.EventHandler")
    def test_adventure_session_fatigue_reduction(self, mock_event, mock_combat, mock_rewards):
        """Verify AdventureSession applies fatigue reduction during Expedition Drive."""
        discord_id = 123
        session = AdventureSession(self.mock_db, self.mock_quest, self.mock_inv, discord_id)
        session.location_id = "forest_outskirts"
        session.active_monster = {"name": "Test Monster"}  # Active monster needed for combat

        # Mock Context Bundle
        bundle = {
            "stats": {"HP": 100, "MP": 100},
            "buffs": [],
            "player": {"current_hp": 100, "current_mp": 100},
            "skills": [],
        }
        self.mock_db.get_combat_context_bundle.return_value = bundle

        # Mock DB returning Expedition Drive boosts
        self.mock_db.get_active_boosts.return_value = []
        self.mock_db.get_active_world_event.return_value = {
            "type": WorldEventSystem.GUILD_EXPEDITION_DRIVE,
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
        # 1.0 (base) * 0.8 (fatigue reduction) = 0.8
        args, kwargs = mock_combat_instance.resolve_turn.call_args
        self.assertAlmostEqual(kwargs["fatigue_multiplier"], 0.8)


if __name__ == "__main__":
    unittest.main()
