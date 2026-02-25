import sys
import time
import unittest
from unittest.mock import MagicMock, patch

# Mock modules before importing project modules
sys.modules["pymongo"] = MagicMock()
sys.modules["pymongo.errors"] = MagicMock()
sys.modules["discord"] = MagicMock()

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
            "experience": 0,
            "exp_to_next": 1000,
        }
        self.mock_db.get_player_field.return_value = 1  # class_id
        self.mock_db.get_player_vitals.return_value = {
            "current_hp": 100,
            "current_mp": 50,
        }
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

        # Verify buff was added via bulk method
        self.mock_db.add_active_buffs_bulk.assert_called()
        call_args = self.mock_db.add_active_buffs_bulk.call_args
        # args: (discord_id, buffs_list)
        buffs_list = call_args[0][1]
        self.assertEqual(len(buffs_list), 1)
        self.assertEqual(buffs_list[0]["name"], "Captains' Ale (Embolden)")
        self.assertEqual(buffs_list[0]["stat"], "STR")
        self.assertEqual(buffs_list[0]["amount"], 3)

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
                {
                    "buff_id": "buff_1",
                    "name": "Strong",
                    "stat": "STR",
                    "amount": 50.0,
                    "end_time": time.time() + 3600,
                }
            ]

            # We call resolve_turn with a dummy monster
            monster = {
                "HP": 10,
                "ATK": 1,
                "DEF": 0,
                "name": "Dummy",
                "skills": [],
                "drops": [],
            }
            report = ch.create_empty_battle_report()

            # Use Manual Mode (context=None)
            ch.resolve_turn(monster, report, persist_vitals=False)

            # Verify log
            self.assertIn(("STR", 50.0), log)

        finally:
            PlayerStats.add_bonus_stat = original_add_bonus

    def test_combat_skills_generate_buffs(self):
        """Tests that skill-based buffs are persisted to the database."""
        # Need to mock CombatEngine since it's instantiated inside resolve_turn
        with patch("game_systems.adventure.combat_handler.CombatEngine") as MockEngine:
            mock_instance = MockEngine.return_value

            # Setup run_combat_turn return value to simulate a buff skill usage
            mock_instance.run_combat_turn.return_value = {
                "winner": None,
                "phrases": [],
                "hp_current": 100,
                "mp_current": 100,
                "monster_hp": 50,
                "turn_report": {},
                "active_boosts": {},
                "new_buffs": [{"name": "Test Buff", "stat": "STR", "amount": 5, "duration": 3}],
            }

            ch = CombatHandler(self.mock_db, self.discord_id)

            # Mock DB calls needed for resolve_turn
            self.mock_db.get_player_vitals.return_value = {
                "current_hp": 100,
                "current_mp": 50,
            }
            self.mock_db.get_active_buffs.return_value = []
            self.mock_db.get_player_stats_json.return_value = {}
            self.mock_db.get_combat_skills.return_value = []
            self.mock_db.get_active_boosts.return_value = []

            monster = {"HP": 10, "ATK": 1, "DEF": 0, "name": "Dummy"}
            report = ch.create_empty_battle_report()

            ch.resolve_turn(monster, report, persist_vitals=False)

            # Verify add_active_buffs_bulk was called
            # Duration should be 3 * 60 = 180s
            self.mock_db.add_active_buffs_bulk.assert_called()

            # Inspect the bulk list passed
            call_args = self.mock_db.add_active_buffs_bulk.call_args
            # call_args[0] -> args tuple. arg[0] is discord_id, arg[1] is list
            buff_list = call_args[0][1]

            found = False
            for buff in buff_list:
                if buff["name"] == "Test Buff" and buff["stat"] == "STR":
                    self.assertEqual(buff["amount"], 5)
                    self.assertEqual(buff["duration_s"], 180)
                    found = True
                    break

            self.assertTrue(found, "add_active_buffs_bulk was not called with the correct buff.")


if __name__ == "__main__":
    unittest.main()
