import sys
import unittest
from unittest.mock import MagicMock, patch

# Mock pymongo before importing anything that uses it
mock_pymongo = MagicMock()
sys.modules["pymongo"] = mock_pymongo

# Now import the modules
from game_systems.adventure.adventure_rewards import AdventureRewards  # noqa: E402


class TestLootLoss(unittest.TestCase):
    def setUp(self):
        self.mock_db = MagicMock()
        self.mock_db.get_player_stats_json.return_value = {
            "strength": {"base": 10, "mod": 0},
            "endurance": {"base": 10, "mod": 0},
            "dexterity": {"base": 10, "mod": 0},
            "agility": {"base": 10, "mod": 0},
            "magic": {"base": 10, "mod": 0},
            "luck": {"base": 10, "mod": 0},
            "hp": 100,
            "mp": 50
        }
        self.mock_inventory_manager = MagicMock()
        self.rewards = AdventureRewards(self.mock_db, 12345)

    @patch('game_systems.adventure.adventure_rewards.item_manager')
    def test_equipment_add_failure_omitted_from_log(self, mock_item_manager):
        # Simulate an equipment drop
        mock_item_manager.generate_monster_loot.return_value = [{
            "id": "item_123",
            "name": "Epic Sword",
            "rarity": "Epic",
            "slot": "main_hand",
            "source": "monster_drop"
        }]

        # Simulate DB failure for adding item
        self.mock_inventory_manager.add_item.return_value = False

        combat_result = {
            "exp": 100,
            "drops": [],
            "monster_data": {"tier": "Normal", "name": "Goblin", "promotion_target": None},
            "active_boosts": {}
        }

        session_loot = {}
        logs = []

        with patch('game_systems.adventure.adventure_rewards.LootCalculator') as mock_loot_calc:
            mock_loot_calc.roll_drops.return_value = []

            # Execute
            self.rewards._process_loot_and_quests(
                combat_result,
                MagicMock(), # quest_system
                self.mock_inventory_manager,
                session_loot,
                logs
            )

        # Check logs for "Epic Sword"
        found_sword = any("Epic Sword" in log for log in logs)

        # Assert that the item IS NOT logged because add_item failed
        self.assertFalse(found_sword, "The item was logged even though add_item failed!")

        # Also verify add_item was called
        self.mock_inventory_manager.add_item.assert_called_once()

if __name__ == '__main__':
    unittest.main()
