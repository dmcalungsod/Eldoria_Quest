import time
import unittest
from unittest.mock import MagicMock

from database.database_manager import DatabaseManager
from game_systems.adventure.combat_handler import CombatHandler
from game_systems.items.consumable_manager import ConsumableManager
from game_systems.player.player_stats import PlayerStats


class TestBuffSystem(unittest.TestCase):
    def setUp(self):
        self.mock_db = MagicMock(spec=DatabaseManager)
        self.discord_id = 12345

        # Default player data
        self.mock_db.get_player.return_value = {
            "discord_id": self.discord_id,
            "name": "TestHero",
            "class_id": 1,
            "level": 1,
        }
        self.mock_db.get_player_field.return_value = 1  # class_id
        self.mock_db.get_player_vitals.return_value = {"current_hp": 100, "current_mp": 50}
        self.mock_db.get_player_stats_json.return_value = {
            "STR": {"base": 10, "bonus": 0},
            "END": {"base": 10, "bonus": 0},
            "DEX": {"base": 10, "bonus": 0},
            "AGI": {"base": 10, "bonus": 0},
            "MAG": {"base": 10, "bonus": 0},
            "LCK": {"base": 10, "bonus": 0},
        }

    def test_buff_lifecycle(self):
        """Tests that buffs are added, retrieved, expire, and cleaned up."""
        buff_record = {
            "discord_id": self.discord_id,
            "buff_id": "test_buff",
            "name": "Test Buff",
            "stat": "STR",
            "amount": 5,
            "end_time": time.time() + 2,
        }

        # Initially: buffs returned
        self.mock_db.get_active_buffs.return_value = [buff_record]
        buffs = self.mock_db.get_active_buffs(self.discord_id)
        self.assertEqual(len(buffs), 1)
        self.assertEqual(buffs[0]["stat"], "STR")
        self.assertEqual(buffs[0]["amount"], 5)

        # After expiry: no buffs
        self.mock_db.get_active_buffs.return_value = []
        buffs = self.mock_db.get_active_buffs(self.discord_id)
        self.assertEqual(len(buffs), 0)

        # Clean expired
        self.mock_db.clear_expired_buffs(self.discord_id)
        self.mock_db.clear_expired_buffs.assert_called_with(self.discord_id)

    def test_consumable_buff_application(self):
        """Tests that using a consumable item applies the correct buff."""
        # Mock inventory item lookup
        self.mock_db.get_inventory_item.return_value = {
            "id": 1,
            "discord_id": self.discord_id,
            "item_key": "strength_brew",
            "item_name": "Brew",
            "item_type": "consumable",
            "count": 1,
        }

        cm = ConsumableManager(self.mock_db)
        success, msg = cm.use_item(self.discord_id, 1)

        self.assertTrue(success)
        self.assertIn("Buffs applied", msg)
        self.assertIn("STR +3", msg)

        # Verify buff was added
        self.mock_db.add_active_buff.assert_called()
        call_args = self.mock_db.add_active_buff.call_args
        self.assertEqual(call_args[0][2], "Captains' Ale (Embolden)")  # name
        self.assertEqual(call_args[0][3], "STR")  # stat
        self.assertEqual(call_args[0][4], 3)  # amount

    def test_combat_handler_applies_buff(self):
        """Tests that CombatHandler applies active buffs to player stats."""
        # Add buff
        self.mock_db.add_active_buff(self.discord_id, "buff_1", "Strong", "STR", 50, 3600)

        # Monkeypatch PlayerStats.add_bonus_stat to verify call
        original_add_bonus = PlayerStats.add_bonus_stat
        log = []

        def mock_add_bonus(self, stat, amount):
            log.append((stat, amount))
            original_add_bonus(self, stat, amount)

        PlayerStats.add_bonus_stat = mock_add_bonus

        try:
            ch = CombatHandler(self.mock_db, self.discord_id)

            # Need valid vitals
            self.mock_db.set_player_vitals(self.discord_id, 100, 50)

            # Mock get_active_buffs to return our buff
            self.mock_db.get_active_buffs.return_value = [
                {"buff_id": "buff_1", "name": "Strong", "stat": "STR", "amount": 50.0, "end_time": time.time() + 3600}
            ]

            # We call resolve_turn with a dummy monster
            monster = {"HP": 10, "ATK": 1, "DEF": 0, "name": "Dummy", "skills": [], "drops": []}
            report = ch.create_empty_battle_report()

            # Use Manual Mode (context=None)
            ch.resolve_turn(monster, report, persist_vitals=False)

            # Verify log
            self.assertIn(("STR", 50.0), log)

        finally:
            PlayerStats.add_bonus_stat = original_add_bonus


if __name__ == "__main__":
    unittest.main()
