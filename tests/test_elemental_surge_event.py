import importlib
import os
import sys
import unittest
import json
from unittest.mock import MagicMock, patch

# Mock pymongo
sys.modules["pymongo"] = MagicMock()
sys.modules["pymongo.errors"] = MagicMock()

# Add repo root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestElementalSurgeEvent(unittest.TestCase):
    def setUp(self):
        # Patch sys.modules
        self.modules_patcher = patch.dict(sys.modules)
        self.modules_patcher.start()

        # Mock Pymongo
        mock_pymongo = MagicMock()
        mock_pymongo.errors = MagicMock()
        sys.modules["pymongo"] = mock_pymongo
        sys.modules["pymongo.errors"] = mock_pymongo.errors

        # Mock Discord
        mock_discord = MagicMock()
        sys.modules["discord"] = mock_discord
        sys.modules["discord.ext"] = MagicMock()

        # Import modules under test
        import database.database_manager
        importlib.reload(database.database_manager)
        self.DatabaseManager = database.database_manager.DatabaseManager

        import game_systems.adventure.adventure_rewards
        importlib.reload(game_systems.adventure.adventure_rewards)
        self.AdventureRewards = game_systems.adventure.adventure_rewards.AdventureRewards

        # Mock DB
        self.mock_db = MagicMock(spec=self.DatabaseManager)
        self.discord_id = 12345
        self.rewards_system = self.AdventureRewards(self.mock_db, self.discord_id)

        # Mock internal systems
        self.rewards_system.rank_system = MagicMock()
        self.rewards_system.achievement_system = MagicMock()
        self.rewards_system.faction_system = MagicMock()
        self.rewards_system.faction_system.grant_reputation_for_kill.return_value = []
        self.rewards_system.achievement_system.check_kill_achievements.return_value = None
        self.rewards_system.achievement_system.check_group_achievements.return_value = None
        self.rewards_system.rank_system.finalize_promotion.return_value = (False, "")

    def tearDown(self):
        self.modules_patcher.stop()

    def test_elemental_surge_drops_mote(self):
        """Verify Elemental Surge event drops Elemental Mote."""
        # Setup Event
        self.mock_db.get_active_world_event.return_value = {
            "type": "elemental_surge",
            "active": 1
        }

        # Setup Player Stats (needed for loot calc)
        self.mock_db.get_player_stats_json.return_value = {"LUCK": 10}

        # Mock Combat Result
        combat_result = {
            "exp": 100,
            "monster_data": {"name": "Test Monster", "tier": "Normal"},
            "drops": [],
            "active_boosts": {}
        }

        session_loot = {}
        quest_system = MagicMock()
        inv_manager = MagicMock()

        # Force random to hit the chance
        with patch("random.random", return_value=0.1): # < 0.3
            with patch("random.randint", return_value=2): # 2 motes
                with patch("game_systems.adventure.adventure_rewards.TournamentSystem") as MockTournament:
                     mock_tournament_instance = MockTournament.return_value

                     self.rewards_system.process_victory(
                         {}, [], combat_result, quest_system, inv_manager, session_loot
                     )

                     # Verify Session Loot has Mote
                     self.assertEqual(session_loot.get("elemental_mote"), 2)

                     # Verify Tournament Record
                     mock_tournament_instance.record_action.assert_any_call(
                         self.discord_id, "elemental_harvest", 2
                     )

    def test_no_event_no_mote(self):
        """Verify no drops when event is not active."""
        self.mock_db.get_active_world_event.return_value = None
        self.mock_db.get_player_stats_json.return_value = {"LUCK": 10}

        combat_result = {
            "exp": 100,
            "monster_data": {"name": "Test Monster", "tier": "Normal"},
            "drops": [],
            "active_boosts": {}
        }

        session_loot = {}

        with patch("game_systems.adventure.adventure_rewards.TournamentSystem") as MockTournament:
             mock_tournament_instance = MockTournament.return_value

             self.rewards_system.process_victory(
                 {}, [], combat_result, MagicMock(), MagicMock(), session_loot
             )

             self.assertIsNone(session_loot.get("elemental_mote"))
             # Ensure record_action was NOT called for elemental_harvest
             # It might be called for monster_kills though
             calls = mock_tournament_instance.record_action.call_args_list
             harvest_calls = [c for c in calls if c.args[1] == "elemental_harvest"]
             self.assertEqual(len(harvest_calls), 0)

if __name__ == "__main__":
    unittest.main()
