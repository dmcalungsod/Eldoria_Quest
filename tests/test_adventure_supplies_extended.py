
import unittest
import json
from unittest.mock import MagicMock, patch
import os
import sys

# Mock pymongo to allow execution without dependencies installed
sys.modules["pymongo"] = MagicMock()
sys.modules["pymongo.errors"] = MagicMock()
sys.modules["discord"] = MagicMock()

# Add repo root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game_systems.adventure.adventure_manager import AdventureManager
from game_systems.adventure.adventure_rewards import AdventureRewards

class TestAdventureEquipmentExtended(unittest.TestCase):
    def setUp(self):
        self.mock_db = MagicMock()
        self.mock_bot = MagicMock()
        self.manager = AdventureManager(self.mock_db, self.mock_bot)
        self.rewards = AdventureRewards(self.mock_db, 12345)

        # Mock dependencies
        self.manager.inventory_manager = MagicMock()
        self.manager.quest_system = MagicMock()
        self.manager.faction_system = MagicMock()

        # Prepare DB mocks
        self.mock_db.get_player_stats_json.return_value = {"strength": 10}
        self.mock_db.get_player.return_value = {
            "level": 1, "experience": 0, "exp_to_next": 100,
            "current_hp": 100, "current_mp": 100
        }
        self.mock_db.lock_adventure_for_claiming.return_value = True

        # FIX: Ensure get_player_field returns integers for level comparison
        def get_field_side_effect(did, field):
            if field == "level": return 1
            return 0
        self.mock_db.get_player_field.side_effect = get_field_side_effect

    def test_identical_equipment_granting(self):
        """
        Verify that identical equipment items dropped in the same combat
        are correctly granted at the end of the adventure (verifying amount > 1).
        """
        discord_id = 12345

        equip_data = {"id": 101, "name": "Fire Sword", "type": "equipment", "rarity": "Rare", "slot": "main_hand", "source": "monster_drop"}
        equip_json = json.dumps(equip_data, sort_keys=True)
        equip_key = f"__EQUIPMENT__:{equip_json}"

        mock_session_row = {
            "discord_id": discord_id,
            "location_id": "test_loc",
            "start_time": "2023-01-01T00:00:00",
            "end_time": "2023-01-01T01:00:00",
            "duration_minutes": 60,
            "active": 1,
            "logs": "[]",
            "loot_collected": json.dumps({equip_key: 3}), # 3 identical Fire Swords
            "active_monster_json": None,
            "version": 1
        }

        self.mock_db.get_active_adventure.return_value = mock_session_row
        self.manager.inventory_manager.add_item.return_value = True

        summary = self.manager.end_adventure(discord_id)

        self.assertIsNotNone(summary)

        # Verify add_item was called 3 times for this item
        self.assertEqual(self.manager.inventory_manager.add_item.call_count, 3)

    def test_json_dumps_key_stability(self):
        """
        Verify that json.dumps key stability doesn't result in multiple entries.
        We test the behavior directly in adventure_rewards to ensure identical
        items end up in the same slot.
        """
        combat_result = {
            "exp": 100,
            "aurum": 50,
            "drops": [],
            "monster_data": {"name": "Test Monster", "tier": "Normal"}
        }

        session_loot = {}

        # Need to mock the generate_monster_loot to return two differently ordered dicts
        # representing the same item
        item_1 = {"id": 1, "name": "Sword", "rarity": "Common"}
        item_2 = {"rarity": "Common", "name": "Sword", "id": 1} # Same data, different insertion order

        with patch("game_systems.items.item_manager.item_manager.generate_monster_loot", return_value=[item_1, item_2]):
            self.rewards._process_loot_and_quests(combat_result, MagicMock(), MagicMock(), session_loot, [])

        # There should only be ONE equipment key in session_loot, with count 2
        equip_keys = [k for k in session_loot.keys() if k.startswith("__EQUIPMENT__:")]
        self.assertEqual(len(equip_keys), 1)
        self.assertEqual(session_loot[equip_keys[0]], 2)

    def test_full_inventory_failure_reporting(self):
        """
        Verify that a full inventory scenario correctly reports both bulk items
        and equipment as failed in the final summary.
        """
        discord_id = 12345

        equip_data = {"id": 101, "name": "Fire Sword", "type": "equipment", "rarity": "Rare", "slot": "main_hand", "source": "monster_drop"}
        equip_json = json.dumps(equip_data, sort_keys=True)
        equip_key = f"__EQUIPMENT__:{equip_json}"

        mock_session_row = {
            "discord_id": discord_id,
            "location_id": "test_loc",
            "start_time": "2023-01-01T00:00:00",
            "end_time": "2023-01-01T01:00:00",
            "duration_minutes": 60,
            "active": 1,
            "logs": "[]",
            "loot_collected": json.dumps({equip_key: 1, "iron_ore": 2}),
            "active_monster_json": None,
            "version": 1
        }

        self.mock_db.get_active_adventure.return_value = mock_session_row

        # Mock Inventory Manager to FAIL EVERYTHING
        self.manager.inventory_manager.add_item.return_value = False
        self.manager.inventory_manager.add_items_bulk.return_value = [{"item_name": "iron_ore", "reason": "Inventory Full"}]

        summary = self.manager.end_adventure(discord_id)

        self.assertIsNotNone(summary)

        # Expect failed items to include both iron ore and the sword
        failed_names = [f["item_name"] for f in summary["failed_items"]]
        self.assertIn("iron_ore", failed_names)
        self.assertIn("Fire Sword", failed_names)

    def test_death_penalty_multiple_units(self):
        """
        Verify that the 50% death loss correctly processes individual equipment units
        when the session loot count is greater than 1.
        """
        discord_id = 12345
        mock_session = MagicMock()
        mock_session.discord_id = discord_id

        equip_data = {"id": 1, "name": "Sword", "rarity": "Common", "slot": "main_hand", "source": "monster_drop"}
        equip_key = f"__EQUIPMENT__:{json.dumps(equip_data, sort_keys=True)}"

        mock_session.loot = {equip_key: 10} # 10 items

        # Force a specific sequence of random rolls (5 True, 5 False)
        with patch("random.random", side_effect=[0.1, 0.9] * 5):
            loss_report = self.manager._handle_death_rewards(discord_id, mock_session)

            # The manager's handle_death_rewards will try to grant the surviving 5 items.
            # So inventory_manager.add_item should be called 5 times.
            self.assertEqual(self.manager.inventory_manager.add_item.call_count, 5)

            # Verify the loss string in report
            self.assertIn("-5x Sword", loss_report)

if __name__ == "__main__":
    unittest.main()
