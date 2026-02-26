import importlib
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Patch sys.modules to mock dependencies BEFORE importing the unit under test
mock_pymongo = MagicMock()
mock_pymongo.errors = MagicMock()
sys.modules["pymongo"] = mock_pymongo
sys.modules["pymongo.errors"] = mock_pymongo.errors

# Mock discord so we don't need real discord.Color
mock_discord = MagicMock()
mock_discord.Color.blue.return_value = 0x3498DB
mock_discord.Color.gold.return_value = 0xF1C40F
sys.modules["discord"] = mock_discord


class MockEmbed:
    def __init__(self, title=None, description=None, color=None, **kwargs):
        self.title = title or ""
        self.description = description or ""
        self.color = color
        self.fields = []

    def set_footer(self, text=None):
        pass

    def add_field(self, name, value, inline=False):
        self.fields.append({"name": name, "value": value})



# Add repo root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import game_systems.guild_system.advisor  # noqa: E402

importlib.reload(game_systems.guild_system.advisor)
from game_systems.guild_system.advisor import GuildAdvisor  # noqa: E402


class TestGuildAdvisorChecklist(unittest.TestCase):
    def setUp(self):
        self.mock_db = MagicMock()
        self.user_id = 12345
        self.advisor = GuildAdvisor(self.mock_db, self.user_id)

        import game_systems.guild_system.advisor
        game_systems.guild_system.advisor.discord.Embed.side_effect = MockEmbed

    def test_get_checklist_embed_brand_new_player(self):
        """Test the checklist for a player with no progress."""
        self.mock_db.get_equipped_items.return_value = []
        self.mock_db.get_guild_member_data.return_value = None
        self.mock_db.get_player_quests_joined.return_value = []
        self.mock_db.get_exploration_stats.return_value = {}

        embed = self.advisor.get_checklist_embed()

        # Should be blue color
        self.assertEqual(embed.color, 0x3498DB)

        # 4 steps should be in the fields
        self.assertEqual(len(embed.fields), 4)

        # Check fields
        fields_text = " ".join([f["value"] or "" for f in embed.fields])
        self.assertEqual(fields_text.count("❌ **Pending**"), 3)  # Steps 2, 3, 4
        self.assertEqual(fields_text.count("✅ **Complete**"), 1)  # Step 1 is always complete

    def test_get_checklist_embed_has_weapon_only(self):
        """Test with weapon equipped but no quests/expeditions."""
        self.mock_db.get_equipped_items.return_value = [{"slot": "sword"}]
        self.mock_db.get_guild_member_data.return_value = {"quests_completed": 0}
        self.mock_db.get_player_quests_joined.return_value = []
        self.mock_db.get_exploration_stats.return_value = {"total_expeditions": 0}

        embed = self.advisor.get_checklist_embed()

        self.assertTrue(any("✅" in f["value"] and "Gear Up" in f["name"] for f in embed.fields))
        self.assertTrue(any("❌" in f["value"] and "First Contract" in f["name"] for f in embed.fields))
        self.assertTrue(any("❌" in f["value"] and "First Expedition" in f["name"] for f in embed.fields))

    def test_get_checklist_embed_has_active_quest(self):
        """Test with active but uncompleted quest."""
        self.mock_db.get_equipped_items.return_value = []
        self.mock_db.get_guild_member_data.return_value = {"quests_completed": 0}
        self.mock_db.get_player_quests_joined.return_value = [{"quest_id": 1}]
        self.mock_db.get_exploration_stats.return_value = {}

        embed = self.advisor.get_checklist_embed()

        self.assertTrue(any("First Contract" in f["name"] and "⚠️" in f["value"] for f in embed.fields))

    def test_get_checklist_embed_all_complete(self):
        """Test graduation state."""
        self.mock_db.get_equipped_items.return_value = [{"slot": "staff"}]
        self.mock_db.get_guild_member_data.return_value = {"quests_completed": 5}
        self.mock_db.get_player_quests_joined.return_value = []
        self.mock_db.get_exploration_stats.return_value = {"total_expeditions": 1}

        embed = self.advisor.get_checklist_embed()

        # Graduated state
        self.assertEqual(embed.color, 0xF1C40F)
        self.assertIn("INITIATION COMPLETE", embed.description)

        self.assertTrue(any("Gear Up" in f["name"] and "✅" in f["value"] for f in embed.fields))
        self.assertTrue(any("First Contract" in f["name"] and "✅" in f["value"] for f in embed.fields))
        self.assertTrue(any("First Expedition" in f["name"] and "✅" in f["value"] for f in embed.fields))


if __name__ == "__main__":
    unittest.main()
