import importlib
import os
import sys
import unittest
from unittest.mock import MagicMock, patch


class TestGuildAdvisor(unittest.TestCase):
    def setUp(self):
        # Patch sys.modules to mock dependencies BEFORE importing the unit under test
        self.modules_patcher = patch.dict(sys.modules)
        self.modules_patcher.start()

        mock_pymongo = MagicMock()
        mock_pymongo.errors = MagicMock()
        sys.modules["pymongo"] = mock_pymongo
        sys.modules["pymongo.errors"] = mock_pymongo.errors
        sys.modules["pymongo.MongoClient"] = MagicMock()

        # Mock Discord
        mock_discord = MagicMock()
        mock_discord.Embed = MagicMock
        mock_discord.Color.blue.return_value = "blue"
        mock_discord.Color.gold.return_value = "gold"
        sys.modules["discord"] = mock_discord

        # Add repo root to path if not present
        repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if repo_root not in sys.path:
            sys.path.insert(0, repo_root)

        # Import modules locally to avoid E402 and ensure mocks are used
        import game_systems.guild_system.advisor
        import game_systems.player.player_stats

        # Reload to ensure we get fresh modules using our mocks
        importlib.reload(game_systems.player.player_stats)
        importlib.reload(game_systems.guild_system.advisor)

        self.GuildAdvisor = game_systems.guild_system.advisor.GuildAdvisor
        self.PlayerStats = game_systems.player.player_stats.PlayerStats

        self.mock_db = MagicMock()
        self.user_id = 12345
        self.advisor = self.GuildAdvisor(self.mock_db, self.user_id)

    def tearDown(self):
        self.modules_patcher.stop()

    def test_low_hp_advice(self):
        """Test advice when HP is critical (< 30%)."""
        # Mock Vitals
        self.mock_db.get_player_vitals.return_value = {"current_hp": 10}

        # Mock Stats (Max HP calculation)
        default_stats = self.PlayerStats().to_dict()
        self.mock_db.get_player_stats_json.return_value = default_stats

        advice = self.advisor.get_advice()
        self.assertTrue(any(x in advice for x in ["Infirmary", "Heal", "wounds"]))

    def test_no_quests_completed(self):
        """Test advice for new players with 0 completed quests."""
        self.mock_db.get_player_vitals.return_value = {"current_hp": 60}
        self.mock_db.get_player_stats_json.return_value = self.PlayerStats().to_dict()
        self.mock_db.get_guild_member_data.return_value = {"quests_completed": 0}

        advice = self.advisor.get_advice()
        self.assertTrue(any(x in advice for x in ["Quest Board", "contracts", "reputation", "Quests"]))

    def test_no_active_quests(self):
        """Test advice when player has no active quests."""
        self.mock_db.get_player_vitals.return_value = {"current_hp": 60}
        self.mock_db.get_player_stats_json.return_value = self.PlayerStats().to_dict()
        self.mock_db.get_guild_member_data.return_value = {"quests_completed": 5}
        self.mock_db.get_player_quests_joined.return_value = []

        advice = self.advisor.get_advice()
        self.assertTrue(any(x in advice for x in ["active contracts", "Idle hands", "monsters are waiting"]))

    def test_rich_but_unarmed(self):
        """Test advice when player has money but no weapon."""
        self.mock_db.get_player_vitals.return_value = {"current_hp": 60}
        self.mock_db.get_player_stats_json.return_value = self.PlayerStats().to_dict()
        self.mock_db.get_guild_member_data.return_value = {"quests_completed": 5}
        self.mock_db.get_player_quests_joined.return_value = [{"id": 1}]
        self.mock_db.get_player.return_value = {"aurum": 1000}
        self.mock_db.get_equipped_items.return_value = []

        advice = self.advisor.get_advice()
        self.assertIn("Shop", advice)

    def test_generic_fallback(self):
        """Test generic advice when all is well."""
        self.mock_db.get_player_vitals.return_value = {"current_hp": 60}
        self.mock_db.get_player_stats_json.return_value = self.PlayerStats().to_dict()
        self.mock_db.get_guild_member_data.return_value = {"quests_completed": 5}
        self.mock_db.get_player_quests_joined.return_value = [{"id": 1}]
        self.mock_db.get_player.return_value = {"aurum": 100}

        advice = self.advisor.get_advice()
        self.assertIsInstance(advice, str)
        self.assertTrue(len(advice) > 10)

    def test_checklist_embed_incomplete(self):
        """Test checklist embed generation for incomplete onboarding."""
        # Setup incomplete state
        self.mock_db.get_equipped_items.return_value = []
        self.mock_db.get_guild_member_data.return_value = {"quests_completed": 0}
        self.mock_db.get_player_quests_joined.return_value = []
        self.mock_db.get_exploration_stats.return_value = {"total_expeditions": 0}

        embed = self.advisor.get_checklist_embed()

        # We mocked discord.Embed, so we inspect calls or properties if we could.
        # But since it's a MagicMock class, the instance is a MagicMock.
        # We can check add_field calls.

        self.assertEqual(embed.add_field.call_count, 4)

        # Check specific field values for Pending status
        calls = embed.add_field.call_args_list

        # Registration (Always Complete)
        self.assertIn("Complete", calls[0].kwargs['value'])

        # Gear Up (Pending)
        self.assertIn("Pending", calls[1].kwargs['value'])

        # First Contract (Pending)
        self.assertIn("Pending", calls[2].kwargs['value'])

        # First Expedition (Pending)
        self.assertIn("Pending", calls[3].kwargs['value'])

    def test_checklist_embed_complete(self):
        """Test checklist embed generation for completed onboarding."""
        # Setup complete state
        self.mock_db.get_equipped_items.return_value = [{"slot": "sword"}]
        self.mock_db.get_guild_member_data.return_value = {"quests_completed": 1}
        self.mock_db.get_player_quests_joined.return_value = []
        self.mock_db.get_exploration_stats.return_value = {"total_expeditions": 1}

        embed = self.advisor.get_checklist_embed()

        self.assertEqual(embed.add_field.call_count, 4)

        calls = embed.add_field.call_args_list
        for call in calls:
            self.assertIn("Complete", call.kwargs['value'])

if __name__ == "__main__":
    unittest.main()
