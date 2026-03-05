import json
import os
import sys
import unittest
from unittest.mock import MagicMock

# Add repo root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock pymongo
mock_pymongo = MagicMock()
mock_pymongo.errors.DuplicateKeyError = Exception
sys.modules["pymongo"] = mock_pymongo
sys.modules["pymongo.errors"] = mock_pymongo.errors

from game_systems.items.equipment_manager import EquipmentManager  # noqa: E402
from game_systems.player.player_stats import PlayerStats  # noqa: E402


class MockDatabaseManager:
    def get_titles(self, discord_id):
        return []

    def __init__(self):
        self.players = {
            123: {
                "discord_id": 123,
                "current_hp": 250,
                "current_mp": 50,
                "class_id": 1,
                "level": 10,
                "stats_json": '{"STR": {"base": 10, "bonus": 0}, "END": {"base": 10, "bonus": 0}}',
                "aurum": 100,
            }
        }
        self.stats = {
            123: {
                "discord_id": 123,
                "stats_json": '{"STR": {"base": 10, "bonus": 0}, "END": {"base": 10, "bonus": 0}}',
            }
        }
        self.inventory = {
            1: {
                "id": 1,
                "discord_id": 123,
                "item_key": "1",
                "item_name": "Helmet",
                "item_type": "equipment",
                "slot": "Head",
                "rarity": "Common",
                "equipped": 1,
                "str_bonus": 0,
                "end_bonus": 10,  # +10 END
                "item_source_table": "equipment",
            }
        }
        self.equipment_data = {1: {"id": 1, "end_bonus": 10, "rarity": "Common", "level_req": 1}}

    def get_player(self, discord_id):
        return self.players.get(discord_id)

    def get_player_stats_json(self, discord_id):
        s = self.stats.get(discord_id, {}).get("stats_json")
        return json.loads(s) if s else {}

    def update_player_stats(self, discord_id, stats_dict):
        # Update stats
        if discord_id in self.stats:
            self.stats[discord_id]["stats_json"] = json.dumps(stats_dict)

    def get_equipped_items(self, discord_id):
        return [i for i in self.inventory.values() if i["discord_id"] == discord_id and i["equipped"] == 1]

    def get_inventory_item(self, discord_id, item_id):
        return self.inventory.get(item_id)

    def set_item_equipped(self, item_id, equipped):
        if item_id in self.inventory:
            self.inventory[item_id]["equipped"] = equipped

    def find_stackable_item(self, *args, **kwargs):
        return None

    def get_all_player_skills(self, discord_id):
        return []

    def get_player_vitals(self, discord_id):
        p = self.players.get(discord_id)
        if p:
            return {
                "current_hp": p.get("current_hp"),
                "current_mp": p.get("current_mp"),
            }
        return None

    def set_player_vitals(self, discord_id, hp, mp):
        if discord_id in self.players:
            self.players[discord_id]["current_hp"] = hp
            self.players[discord_id]["current_mp"] = mp

    def _col(self, name):
        # Mock collection for item lookup
        m = MagicMock()

        def find_one(query, projection=None):
            if name == "equipment":
                return self.equipment_data.get(int(query.get("id")))
            return None

        m.find_one.side_effect = find_one

        # Add update_one mock
        m.update_one = MagicMock()
        m.delete_one = MagicMock()

        return m

    def get_guild_rank(self, discord_id):
        return "F"

    def get_active_buffs(self, discord_id):
        return []

    def get_equipped_in_slot(self, discord_id, slot):
        for item in self.inventory.values():
            if item["discord_id"] == discord_id and item.get("slot") == slot and item.get("equipped") == 1:
                return item
        return None

    def decrement_inventory_count(self, item_id):
        pass

    def get_player_field(self, discord_id, field):
        return self.players.get(discord_id, {}).get(field)


class TestHPOverflow(unittest.TestCase):
    def test_hp_clamp_on_unequip(self):
        db = MockDatabaseManager()
        manager = EquipmentManager(db)

        # Setup: Player has item equipped (+10 END)
        # Recalculate stats to ensure we are in sync
        stats = manager.recalculate_player_stats(123)
        # Base END 10 + Bonus 10 = 20 END
        # Max HP = 50 + 20*10 = 250

        self.assertEqual(stats.endurance, 20)
        self.assertEqual(stats.max_hp, 250)

        # Simulate full HP
        db.players[123]["current_hp"] = 250

        # Unequip item
        success, msg = manager.unequip_item(123, 1)
        self.assertTrue(success, f"Unequip failed: {msg}")

        # Verify item unequipped
        self.assertEqual(db.inventory[1]["equipped"], 0)

        # Verify stats recalculated
        # We can fetch fresh stats from DB or just check if update_player_stats was called (it updates self.stats)
        fresh_stats_json = db.get_player_stats_json(123)
        fresh_stats = PlayerStats.from_dict(fresh_stats_json)

        self.assertEqual(fresh_stats.endurance, 10)  # Base 10, Bonus 0
        self.assertEqual(fresh_stats.max_hp, 150)  # 50 + 10*10

        # Verify Current HP is clamped
        current_hp = db.players[123]["current_hp"]
        print(f"Current HP after unequip: {current_hp}")

        # BUG: Current HP is likely still 250 because unequip_item doesn't clamp
        self.assertLessEqual(current_hp, 150, f"HP Overflow! Current: {current_hp}, Max allowed: 150")

    def test_hp_clamp_with_buffs(self):
        db = MockDatabaseManager()
        # Mock active buffs: +15 END => +150 HP
        db.get_active_buffs = MagicMock(
            return_value=[{"discord_id": 123, "stat": "END", "amount": 15, "name": "Giant Growth", "duration": 3600}]
        )

        manager = EquipmentManager(db)

        # Setup: Player has item equipped (+10 END) AND Buff (+15 END)
        # Base 10 + Item 10 + Buff 15 = 35 END

        # 1. Equip Item manually first to setup state
        # The manager.recalculate_player_stats call inside equip/unequip resets bonuses
        # so we rely on db.inventory having equipped=1 for the item.

        # Simulate stats BEFORE unequip:
        # We need to ensure manager sees the item as equipped.
        # Recalculate will see item (10 END) and apply it.
        # But buffs are applied ONLY for clamping check, NOT persisted to stats_json.

        stats = manager.recalculate_player_stats(123)
        # Persistent Stats (saved to DB): Base 10 + Item 10 = 20 END
        # Max HP (Persistent) = 50 + 20*10 = 250.

        self.assertEqual(stats.endurance, 20)
        self.assertEqual(stats.max_hp, 250)

        # With Buff (+15 END -> +150 HP), Total Max HP is ~400.
        # We set current HP to 400.
        db.players[123]["current_hp"] = 400

        # Unequip item (+10 END)
        # New Persistent Stats: Base 10 = 10 END -> 150 HP
        # Buff remains: +15 END -> +150 HP
        # New Total Max HP: 150 + 150 = 300

        success, msg = manager.unequip_item(123, 1)
        self.assertTrue(success, f"Unequip failed: {msg}")

        # Verify Current HP is clamped to Total Max HP (300), NOT Persistent Max HP (150)
        current_hp = db.players[123]["current_hp"]
        print(f"Current HP after unequip with buffs: {current_hp}")

        # It should be > 150 because of the buff
        self.assertGreater(
            current_hp, 150, f"HP Clamped too aggressively! Current: {current_hp}, Expected > 150 (due to buff)"
        )
        self.assertLessEqual(current_hp, 305, f"HP Overflow! Current: {current_hp}, Max allowed: ~300")


if __name__ == "__main__":
    unittest.main()
