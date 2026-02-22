import sys
import unittest
from unittest.mock import MagicMock, patch
import os

# Adjust path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock external dependencies before importing AdventureRewards
sys.modules["database.database_manager"] = MagicMock()
sys.modules["game_systems.achievement_system"] = MagicMock()
sys.modules["game_systems.guild_system.faction_system"] = MagicMock()
sys.modules["game_systems.guild_system.rank_system"] = MagicMock()
sys.modules["game_systems.guild_system.tournament_system"] = MagicMock()
sys.modules["game_systems.items.item_manager"] = MagicMock()
sys.modules["game_systems.player.player_stats"] = MagicMock()
sys.modules["game_systems.rewards.loot_calculator"] = MagicMock()

from game_systems.adventure.adventure_rewards import AdventureRewards

class TestNarrativeQuest(unittest.TestCase):
    def setUp(self):
        self.mock_db = MagicMock()
        self.mock_quest_system = MagicMock()
        self.rewards = AdventureRewards(self.mock_db, 12345)

    def test_update_quests_flavor_text_defeat(self):
        # Setup Quest with flavor text
        quest_data = {
            "id": 1,
            "title": "Narrative Quest",
            "objectives": {
                "defeat": {"Slime": 5}
            },
            "flavor_text": {
                "defeat:Slime": "The slime wobbles sadly before dying."
            }
        }

        self.mock_quest_system.get_player_quests.return_value = [quest_data]
        self.mock_quest_system.update_progress.return_value = True

        logs = []
        actual_drops = []
        monster_name = "Slime"

        # Act
        self.rewards._update_quests(self.mock_quest_system, monster_name, actual_drops, logs)

        # Assert
        self.assertIn("\n*The slime wobbles sadly before dying.*", logs)
        self.mock_quest_system.update_progress.assert_called_with(12345, 1, "defeat", "Slime")

    def test_update_quests_flavor_text_collect(self):
        # Setup Quest with flavor text
        quest_data = {
            "id": 1,
            "title": "Narrative Quest",
            "objectives": {
                "collect": {"Slime Gel": 3}
            },
            "flavor_text": {
                "collect:Slime Gel": "Eww, it's sticky."
            }
        }

        self.mock_quest_system.get_player_quests.return_value = [quest_data]
        self.mock_quest_system.update_progress.return_value = True

        logs = []
        actual_drops = ["Slime Gel"]
        monster_name = "Slime"

        # Act
        self.rewards._update_quests(self.mock_quest_system, monster_name, actual_drops, logs)

        # Assert
        self.assertIn("\n*Eww, it's sticky.*", logs)
        self.mock_quest_system.update_progress.assert_called_with(12345, 1, "collect", "Slime Gel")

    def test_update_quests_no_spam(self):
        # Setup Quest with flavor text
        quest_data = {
            "id": 1,
            "title": "Narrative Quest",
            "objectives": {
                "collect": {"Slime Gel": 3}
            },
            "flavor_text": {
                "collect:Slime Gel": "Eww, it's sticky."
            }
        }

        self.mock_quest_system.get_player_quests.return_value = [quest_data]
        self.mock_quest_system.update_progress.return_value = True

        logs = []
        actual_drops = ["Slime Gel", "Slime Gel"] # Two drops
        monster_name = "Slime"

        # Act
        self.rewards._update_quests(self.mock_quest_system, monster_name, actual_drops, logs)

        # Assert
        # Count occurrences of the flavor text
        flavor_count = sum(1 for log in logs if "*Eww, it's sticky.*" in log)
        self.assertEqual(flavor_count, 1, "Flavor text should only appear once per update call")
        # But update_progress should be called twice
        self.assertEqual(self.mock_quest_system.update_progress.call_count, 2)

if __name__ == '__main__':
    unittest.main()
