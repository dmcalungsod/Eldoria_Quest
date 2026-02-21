import os
import sys
import unittest
from unittest.mock import MagicMock

# Mock pymongo BEFORE importing modules that use it
sys.modules["pymongo"] = MagicMock()
sys.modules["pymongo.errors"] = MagicMock()
sys.modules["pymongo.MongoClient"] = MagicMock()

# Add repo root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game_systems.guild_system.advisor import GuildAdvisor  # noqa: E402
from game_systems.player.player_stats import PlayerStats  # noqa: E402


class TestGuildAdvisor(unittest.TestCase):
    def setUp(self):
        self.mock_db = MagicMock()
        self.user_id = 12345
        self.advisor = GuildAdvisor(self.mock_db, self.user_id)

    def test_low_hp_advice(self):
        """Test advice when HP is critical (< 30%)."""
        # Mock Vitals
        self.mock_db.get_player_vitals.return_value = {"current_hp": 10}

        # Mock Stats (Max HP calculation)
        # Default stats give 50 + (1 * 10) = 60 HP. 10/60 = 0.16 < 0.3
        default_stats = PlayerStats().to_dict()
        # Ensure to_dict returns what get_player_stats_json expects
        # get_player_stats_json returns dict from json.loads
        self.mock_db.get_player_stats_json.return_value = default_stats

        advice = self.advisor.get_advice()
        # Check for keywords related to Infirmary/healing
        self.assertTrue(any(x in advice for x in ["Infirmary", "Heal", "wounds"]))

    def test_no_quests_completed(self):
        """Test advice for new players with 0 completed quests."""
        # Healthy (60 HP / 60 Max)
        self.mock_db.get_player_vitals.return_value = {"current_hp": 60}
        self.mock_db.get_player_stats_json.return_value = PlayerStats().to_dict()

        # 0 Quests Completed
        self.mock_db.get_guild_member_data.return_value = {"quests_completed": 0}

        advice = self.advisor.get_advice()
        self.assertTrue(any(x in advice for x in ["Quest Board", "contracts", "reputation", "Quests"]))

    def test_no_active_quests(self):
        """Test advice when player has no active quests."""
        # Healthy
        self.mock_db.get_player_vitals.return_value = {"current_hp": 60}
        self.mock_db.get_player_stats_json.return_value = PlayerStats().to_dict()

        # Has completed quests
        self.mock_db.get_guild_member_data.return_value = {"quests_completed": 5}

        # No active quests
        self.mock_db.get_player_quests_joined.return_value = []

        advice = self.advisor.get_advice()
        self.assertTrue(any(x in advice for x in ["active contracts", "Idle hands", "monsters are waiting"]))

    def test_rich_but_unarmed(self):
        """Test advice when player has money but no weapon."""
        # Healthy
        self.mock_db.get_player_vitals.return_value = {"current_hp": 60}
        self.mock_db.get_player_stats_json.return_value = PlayerStats().to_dict()

        # Has quests and active quest
        self.mock_db.get_guild_member_data.return_value = {"quests_completed": 5}
        self.mock_db.get_player_quests_joined.return_value = [{"id": 1}]

        # Rich
        self.mock_db.get_player.return_value = {"aurum": 1000}

        # No weapon
        self.mock_db.get_equipped_items.return_value = []

        advice = self.advisor.get_advice()
        self.assertIn("Shop", advice)

    def test_generic_fallback(self):
        """Test generic advice when all is well."""
        # Healthy
        self.mock_db.get_player_vitals.return_value = {"current_hp": 60}
        self.mock_db.get_player_stats_json.return_value = PlayerStats().to_dict()

        # Has quests and active quest
        self.mock_db.get_guild_member_data.return_value = {"quests_completed": 5}
        self.mock_db.get_player_quests_joined.return_value = [{"id": 1}]

        # Not rich
        self.mock_db.get_player.return_value = {"aurum": 100}

        advice = self.advisor.get_advice()
        # Just ensure we got something stringy and not None
        self.assertIsInstance(advice, str)
        self.assertTrue(len(advice) > 10)

if __name__ == "__main__":
    unittest.main()
