import importlib
import os
import sys
import unittest
from unittest.mock import MagicMock, patch



class MockField:
    def __init__(self, name, value, inline):
        self.name = name
        self.value = value
        self.inline = inline

class MockEmbed:
    def __init__(self, title=None, description=None, color=None):
        self.title = title
        self.description = description
        self.color = color
        self.fields = []

    def add_field(self, name, value, inline):
        self.fields.append(MockField(name, value, inline))

class TestGuildAdvisor(unittest.TestCase):
    def setUp(self):
        # Patch sys.modules to mock dependencies BEFORE importing the unit under test

        mock_discord = MagicMock()
        mock_discord.Embed = MockEmbed
        mock_discord.Color.blue.return_value = "blue"
        mock_discord.Color.gold.return_value = "gold"

        mock_pymongo = MagicMock()
        mock_pymongo.errors = MagicMock()

        self.modules_patcher = patch.dict('sys.modules', {
            "pymongo": mock_pymongo,
            "pymongo.errors": mock_pymongo.errors,
            "pymongo.MongoClient": MagicMock(),
            "discord": mock_discord
        })
        self.modules_patcher.start()

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



    def test_checklist_embed_all_pending(self):
        """Test checklist embed when all criteria are pending."""
        self.mock_db.get_equipped_items.return_value = []
        self.mock_db.get_guild_member_data.return_value = {"quests_completed": 0}
        self.mock_db.get_player_quests_joined.return_value = []
        self.mock_db.get_exploration_stats.return_value = {"total_expeditions": 0}

        embed = self.advisor.get_checklist_embed()

        self.assertEqual(embed.title, "📜 New Recruit Checklist")
        self.assertEqual(embed.color, sys.modules["discord"].Color.blue())

        fields = embed.fields
        self.assertEqual(len(fields), 4)

        self.assertEqual(fields[0].name, "1. Registration")
        self.assertIn("✅", fields[0].value)

        self.assertEqual(fields[1].name, "2. Gear Up")
        self.assertIn("❌", fields[1].value)

        self.assertEqual(fields[2].name, "3. First Contract")
        self.assertIn("❌", fields[2].value)

        self.assertEqual(fields[3].name, "4. First Expedition")
        self.assertIn("❌", fields[3].value)

    def test_checklist_embed_completed_initiation(self):
        """Test checklist embed when all criteria are met and player graduates."""
        self.mock_db.get_equipped_items.return_value = [{"slot": "sword"}]
        self.mock_db.get_guild_member_data.return_value = {"quests_completed": 1}
        self.mock_db.get_player_quests_joined.return_value = []
        self.mock_db.get_exploration_stats.return_value = {"total_expeditions": 1}

        embed = self.advisor.get_checklist_embed()

        self.assertEqual(embed.color, sys.modules["discord"].Color.gold())
        self.assertIn("INITIATION COMPLETE", embed.description)

        fields = embed.fields
        self.assertEqual(len(fields), 4)

        self.assertEqual(fields[0].name, "1. Registration")
        self.assertIn("✅", fields[0].value)

        self.assertEqual(fields[1].name, "2. Gear Up")
        self.assertIn("✅", fields[1].value)

        self.assertEqual(fields[2].name, "3. First Contract")
        self.assertIn("✅", fields[2].value)

        self.assertEqual(fields[3].name, "4. First Expedition")
        self.assertIn("✅", fields[3].value)


if __name__ == "__main__":
    unittest.main()
