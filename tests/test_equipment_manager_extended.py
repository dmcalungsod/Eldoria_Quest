import unittest
from unittest.mock import MagicMock, patch
from game_systems.items.equipment_manager import EquipmentManager
from game_systems.player.player_stats import PlayerStats


class TestEquipmentManagerExtended(unittest.TestCase):
    def setUp(self):
        self.mock_db = MagicMock()
        self.stats = PlayerStats()
        self.manager = EquipmentManager(self.mock_db)

    def test_equip_item_success(self):
        player_id = 123
        item = {
            "id": 101,
            "item_key": "iron_armor",
            "item_type": "equipment",
            "slot": "chest",
            "rarity": "Common",
            "count": 1,
        }
        self.mock_db.get_inventory_item.return_value = item
        self.mock_db.get_player.return_value = {"class_id": 1}
        self.mock_db.get_guild_rank.return_value = "F"
        self.mock_db.get_equipped_items.return_value = []
        self.mock_db.get_player_stats_json.return_value = {}
        self.mock_db.get_player_vitals.return_value = {"current_hp": 100, "current_mp": 50}
        self.mock_db.get_player_field.return_value = 1  # Mock class_id for _get_player_allowed_slots

        # Manually inject a class with the 'chest' slot allowed to CLASSES
        with patch.dict("game_systems.data.class_data.CLASSES", {"Warrior": {"id": 1, "allowed_slots": ["chest"]}}):
            success, msg = self.manager.equip_item(player_id, 101)

            self.assertTrue(success, f"Equip failed: {msg}")
            self.mock_db.set_item_equipped.assert_called_with(101, 1)

    def test_unequip_item(self):
        player_id = 123
        item = {"id": 101, "equipped": 1, "item_key": "iron_armor", "rarity": "Common", "slot": "chest"}
        self.mock_db.get_inventory_item.return_value = item
        self.mock_db.find_stackable_item.return_value = None
        self.mock_db.get_player_stats_json.return_value = {}
        self.mock_db.get_player_vitals.return_value = {"current_hp": 100, "current_mp": 50}

        success, msg = self.manager.unequip_item(player_id, 101)

        self.assertTrue(success)
        self.mock_db.set_item_equipped.assert_called_with(101, 0)


if __name__ == "__main__":
    unittest.main()
