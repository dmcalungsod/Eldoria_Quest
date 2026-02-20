import unittest
from unittest.mock import MagicMock

from game_systems.items.equipment_manager import EquipmentManager


class TestStatDuplication(unittest.TestCase):
    def setUp(self):
        self.mock_db = MagicMock()
        self.equipment_manager = EquipmentManager(self.mock_db)

    def test_recalculate_stats_duplication(self):
        # 1. Setup initial stats (Base 10, Bonus 0)
        initial_stats = {
            "STR": {"base": 10, "bonus": 0},
            "END": {"base": 10, "bonus": 0},
            "DEX": {"base": 10, "bonus": 0},
            "AGI": {"base": 10, "bonus": 0},
            "MAG": {"base": 10, "bonus": 0},
            "LCK": {"base": 10, "bonus": 0},
        }
        self.mock_db.get_player_stats_json.return_value = initial_stats

        # Mock get_player_vitals to prevent clamping error
        self.mock_db.get_player_vitals.return_value = {"current_hp": 100, "current_mp": 50}

        # 2. Setup equipped item (+5 STR)
        # Mock get_equipped_items to return one item
        self.mock_db.get_equipped_items.return_value = [{"item_key": "101", "item_source_table": "equipment"}]

        # Mock item data lookup
        # item_source_table is 'equipment', so it calls _col('equipment').find_one
        mock_collection = MagicMock()
        mock_collection.find_one.return_value = {
            "id": 101,
            "str_bonus": 5,
            # other bonuses 0 or missing
        }
        self.mock_db._col.return_value = mock_collection

        self.mock_db.get_player_field.return_value = 1  # class_id

        # 3. First Recalculation
        stats1 = self.equipment_manager.recalculate_player_stats(123)

        # Verify first calculation is correct
        self.assertEqual(stats1.strength, 15)  # 10 base + 5 bonus
        self.assertEqual(stats1._stats["STR"].bonus, 5)

        # 4. Simulate saving the state
        # We manually update the return value of get_player_stats_json to reflect what was "saved"
        # The bug was that the saved JSON contained the bonus, and subsequent loads would keep it.
        saved_stats_1 = stats1.to_dict()
        self.mock_db.get_player_stats_json.return_value = saved_stats_1

        # 5. Second Recalculation (No new items, just recalculating)
        stats2 = self.equipment_manager.recalculate_player_stats(123)

        # 6. Verify if duplication occurred
        # With the fix, bonuses should be reset before adding item bonuses again.
        self.assertEqual(stats2.strength, 15, "Strength should remain 15 (10+5).")
        self.assertEqual(stats2._stats["STR"].bonus, 5, "Bonus should remain 5.")


if __name__ == "__main__":
    unittest.main()
