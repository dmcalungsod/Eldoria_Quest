import json
import os
import sys
import unittest
from unittest.mock import MagicMock

# Ensure root is in path
sys.path.append(os.getcwd())

# Mock pymongo
sys.modules["pymongo"] = MagicMock()
sys.modules["pymongo.errors"] = MagicMock()

# Import after mocking
from game_systems.guild_system.reward_system import RewardSystem  # noqa: E402


class TestRewardSystemMaterials(unittest.TestCase):
    def setUp(self):
        self.mock_db = MagicMock()
        # Mock InventoryManager inside RewardSystem to prevent it from doing anything
        # Also need to patch DatabaseManager since RewardSystem imports it

        # Manually set attributes on the mock_db that RewardSystem uses
        self.mock_db._col = MagicMock()
        self.mock_db.get_player = MagicMock()
        self.mock_db.get_player_stats_json = MagicMock()
        self.mock_db.grant_quest_rewards = MagicMock()
        self.mock_db.add_inventory_item = MagicMock()

        # Instantiate RewardSystem with our mock DB
        self.reward_system = RewardSystem(self.mock_db)

        # We need to ensure InventoryManager doesn't blow up if initialized
        self.reward_system.inv_manager = MagicMock()
        self.reward_system.achievement_system = MagicMock()

    def test_grant_material_reward(self):
        # Setup Quest Data with a Material Reward
        quest_id = 999
        quest_data = {
            "id": quest_id,
            "title": "Test Quest",
            "rewards": json.dumps(
                {
                    "exp": 100,
                    "aurum": 50,
                    "item": "Magic Stone (Small)",  # This is a Material
                }
            ),
        }

        # Setup DB Mocks
        # find_one is called to get quest details
        self.mock_db._col.return_value.find_one.return_value = quest_data

        # get_player returns basic player info
        self.mock_db.get_player.return_value = {"level": 1, "experience": 0, "exp_to_next": 100}
        self.mock_db.get_player_stats_json.return_value = None

        # Execute
        discord_id = 12345
        result_msg = self.reward_system.grant_rewards(discord_id, quest_id)

        # Verify
        self.mock_db.add_inventory_item.assert_called()

        call_args = self.mock_db.add_inventory_item.call_args[0]

        self.assertEqual(call_args[0], discord_id)
        self.assertEqual(call_args[1], "magic_stone_small")  # Key from materials.py
        self.assertEqual(call_args[2], "Magic Stone (Small)")
        self.assertEqual(call_args[3], "material")  # Type should be 'material'
        self.assertEqual(call_args[4], "Common")  # Rarity
        self.assertEqual(call_args[5], 1)  # Amount

        # Check message contains item acquired
        self.assertIn("Magic Stone (Small)", result_msg)

    def test_grant_frostfall_reward(self):
        # Setup Quest Data with a Frostfall Material Reward
        quest_id = 998
        quest_data = {
            "id": quest_id,
            "title": "Frozen Echo Test",
            "rewards": json.dumps({"exp": 100, "aurum": 50, "item": "Ice Core"}),
        }

        self.mock_db._col.return_value.find_one.return_value = quest_data
        self.mock_db.get_player.return_value = {"level": 1, "experience": 0, "exp_to_next": 100}
        self.mock_db.get_player_stats_json.return_value = None

        # Execute
        discord_id = 12345
        result_msg = self.reward_system.grant_rewards(discord_id, quest_id)

        # Verify
        self.mock_db.add_inventory_item.assert_called()
        call_args = self.mock_db.add_inventory_item.call_args[0]

        self.assertEqual(call_args[1], "ice_core")  # Key from materials.py
        self.assertEqual(call_args[2], "Ice Core")
        self.assertEqual(call_args[3], "material")  # Type should be 'material'
        self.assertIn("Ice Core", result_msg)

    def test_grant_consumable_reward(self):
        # Setup Quest Data with a Consumable Reward
        quest_id = 888
        quest_data = {
            "id": quest_id,
            "title": "Test Quest Consumable",
            "rewards": json.dumps(
                {
                    "exp": 100,
                    "aurum": 50,
                    "item": "Dewfall Tonic",  # This is a Consumable
                }
            ),
        }

        self.mock_db._col.return_value.find_one.return_value = quest_data
        self.mock_db.get_player.return_value = {"level": 1, "experience": 0, "exp_to_next": 100}
        self.mock_db.get_player_stats_json.return_value = None

        # Execute
        discord_id = 12345
        self.reward_system.grant_rewards(discord_id, quest_id)

        # Verify
        self.mock_db.add_inventory_item.assert_called()
        call_args = self.mock_db.add_inventory_item.call_args[0]

        self.assertEqual(call_args[1], "hp_potion_1")  # Key from consumables.json
        self.assertEqual(call_args[3], "consumable")  # Type should be 'consumable'


if __name__ == "__main__":
    unittest.main()
