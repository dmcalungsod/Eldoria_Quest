import os
import sys
import unittest
from unittest.mock import MagicMock

# Mock pymongo
sys.modules["pymongo"] = MagicMock()
sys.modules["pymongo.errors"] = MagicMock()

# Add repo root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game_systems.data.class_data import CLASSES
from game_systems.items.consumable_manager import ConsumableManager
from game_systems.items.equipment_manager import EquipmentManager
from game_systems.player.player_stats import PlayerStats


class TestAlchemistMechanics(unittest.TestCase):
    def setUp(self):
        self.mock_db = MagicMock()
        self.cm = ConsumableManager(self.mock_db)
        self.em = EquipmentManager(self.mock_db)
        self.discord_id = 12345

    def test_class_data_exists(self):
        """Verify Alchemist class exists in data."""
        self.assertIn("Alchemist", CLASSES)
        self.assertEqual(CLASSES["Alchemist"]["id"], 6)

    def test_triage_healing_bonus(self):
        """Verify Triage skill increases healing item potency."""
        # Mock Inventory Item
        self.mock_db.get_inventory_item.return_value = {
            "item_key": "hp_potion_1",
            "item_type": "consumable",
            "name": "Dewfall Tonic",
        }

        # Mock Player Vitals (injured)
        self.mock_db.get_player_vitals.return_value = {"current_hp": 10, "current_mp": 10}
        self.mock_db.get_player_stats_json.return_value = PlayerStats(end_base=10).to_dict()

        # Mock consume success
        self.mock_db.consume_item_atomic.return_value = True

        # Case 1: No Triage Skill
        self.mock_db.get_player_skill_levels.return_value = {}

        success, msg = self.cm.use_item(self.discord_id, 1)
        self.assertTrue(success)
        # Expected heal: 50
        self.assertIn("healed for 50 HP", msg)

        # Case 2: Triage Level 1 (+20%)
        self.mock_db.get_player_skill_levels.return_value = {"triage": 1}

        # Reset vitals for next call (mocking state change if needed, but here inputs are mocked)

        success, msg = self.cm.use_item(self.discord_id, 1)
        self.assertTrue(success)
        # Expected heal: 50 * 1.2 = 60
        self.assertIn("healed for 60 HP", msg)
        self.assertIn("Boosted x1.2", msg)

        # Case 3: Triage Level 5 (Base 20% + 4*2% = 28% -> 1.28x)
        self.mock_db.get_player_skill_levels.return_value = {"triage": 5}

        success, msg = self.cm.use_item(self.discord_id, 1)
        self.assertTrue(success)
        # Expected heal: 50 * 1.28 = 64
        self.assertIn("healed for 64 HP", msg)
        self.assertIn("Boosted x1.3", msg)

    def test_equivalent_exchange_stat_bonus(self):
        """Verify Equivalent Exchange skill increases MAG."""
        # Mock Player Stats
        base_stats = PlayerStats(mag_base=10)
        self.mock_db.get_player_stats_json.return_value = base_stats.to_dict()

        # Mock Equipment (Empty)
        self.mock_db.get_equipped_items.return_value = []

        # Mock Skills
        self.mock_db.get_all_player_skills.return_value = [{"skill_key": "equivalent_exchange", "skill_level": 1}]

        # Mock DB Vitals (to avoid clamp error)
        self.mock_db.get_player_vitals.return_value = {"current_hp": 100, "current_mp": 100}

        # Run Recalculation
        stats = self.em.recalculate_player_stats(self.discord_id)

        # MAG Base 10. Bonus: 10 * 0.1 * 1 = 1. Total MAG = 11.
        # Stats object should have bonus applied.

        # Check calling update_player_stats with correct data
        self.mock_db.update_player_stats.assert_called()
        call_args = self.mock_db.update_player_stats.call_args[0]
        saved_stats_dict = call_args[1]

        # Reconstruct to check values
        saved_stats = PlayerStats.from_dict(saved_stats_dict)
        self.assertEqual(saved_stats.magic, 11)


if __name__ == "__main__":
    unittest.main()
