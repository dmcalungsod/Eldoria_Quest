import asyncio
import os
import sys
import unittest
from unittest.mock import MagicMock

# Mock pymongo with a real DuplicateKeyError exception class
mock_pymongo = MagicMock()


class _DuplicateKeyError(Exception):
    pass


mock_pymongo.errors.DuplicateKeyError = _DuplicateKeyError
sys.modules["pymongo"] = mock_pymongo
sys.modules["pymongo.errors"] = mock_pymongo.errors

import threading  # noqa: E402
import time  # noqa: E402

import pymongo.errors  # noqa: E402

# Add repo root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Force reload so equipment_manager picks up our mock_pymongo
import importlib  # noqa: E402

import game_systems.items.equipment_manager as _em_mod  # noqa: E402

importlib.reload(_em_mod)

from game_systems.items.equipment_manager import EquipmentManager  # noqa: E402


class MockDatabaseManager:
    def __init__(self):
        self.inventory = {}  # id -> item
        self.unique_constraint = set()  # (discord_id, slot) where equipped=1
        self.enforce_constraint = True  # Toggle to simulate DB fix
        self.barrier = threading.Barrier(2)  # Synchronize 2 threads

    def get_inventory_item(self, discord_id, inv_id):
        return self.inventory.get(inv_id)

    def get_equipped_in_slot(self, discord_id, slot):
        # Sync threads so they both check at the same time
        try:
            self.barrier.wait(timeout=1.0)
        except threading.BrokenBarrierError:
            pass

        # Simulate Read Latency
        time.sleep(0.1)

        for item in self.inventory.values():
            if (
                item["discord_id"] == discord_id
                and item.get("slot") == slot
                and item.get("equipped") == 1
            ):
                return item
        return None

    def set_item_equipped(self, inv_id, equipped):
        item = self.inventory.get(inv_id)
        if not item:
            return

        # Simulate Write Latency
        time.sleep(0.05)

        if self.enforce_constraint and equipped == 1:
            key = (item["discord_id"], item["slot"])
            if key in self.unique_constraint:
                raise pymongo.errors.DuplicateKeyError("E11000 duplicate key error")
            self.unique_constraint.add(key)

        # If un-equipping, remove from constraint
        if self.enforce_constraint and equipped == 0:
            key = (item["discord_id"], item["slot"])
            if key in self.unique_constraint:
                try:
                    self.unique_constraint.remove(key)
                except KeyError:
                    pass

        item["equipped"] = equipped

    def _col(self, name):
        mock_col = MagicMock()
        return mock_col

    def find_stackable_item(self, *args, **kwargs):
        return None

    def decrement_inventory_count(self, inv_id):
        pass

    def recalculate_player_stats(self, discord_id):
        pass

    def get_equipped_items(self, discord_id):
        return [
            item
            for item in self.inventory.values()
            if item["discord_id"] == discord_id and item.get("equipped") == 1
        ]

    def update_player_stats(self, *args):
        pass

    def get_player_stats_json(self, *args):
        return {}

    def get_all_player_skills(self, *args):
        return []

    def get_player_field(self, discord_id, field):
        return 1

    def get_player(self, discord_id):
        return {"level": 10, "class_id": 1}

    def get_guild_rank(self, discord_id):
        return "F"

    def get_player_vitals(self, discord_id):
        return {"current_hp": 100, "current_mp": 20}

    def set_player_vitals(self, discord_id, hp, mp):
        pass

    def _unequip_logic(self, discord_id, inv_id):
        self.set_item_equipped(inv_id, 0)


class TestEquipmentRaceMock(unittest.IsolatedAsyncioTestCase):
    async def test_race_condition(self):
        """Verifies that concurrent equip requests for the same slot are handled safely."""
        db = MockDatabaseManager()
        # Initial State
        db.inventory = {
            101: {
                "id": 101,
                "discord_id": 12345,
                "item_type": "equipment",
                "slot": "Head",
                "equipped": 0,
                "item_key": "101",
                "rarity": "Common",
                "item_name": "Helm A",
            },
            102: {
                "id": 102,
                "discord_id": 12345,
                "item_type": "equipment",
                "slot": "Head",
                "equipped": 0,
                "item_key": "102",
                "rarity": "Common",
                "item_name": "Helm B",
            },
        }

        manager = EquipmentManager(db)
        manager._get_player_allowed_slots = MagicMock(return_value=["Head"])

        loop = asyncio.get_running_loop()

        def equip_task(item_id):
            return manager.equip_item(12345, item_id)

        # Execute concurrent tasks
        fut1 = loop.run_in_executor(None, equip_task, 101)
        fut2 = loop.run_in_executor(None, equip_task, 102)

        await asyncio.gather(fut1, fut2)

        equipped_count = sum(1 for i in db.inventory.values() if i["equipped"] == 1)

        # Verify Fix: Only one item should be equipped
        self.assertEqual(
            equipped_count, 1, "Race condition persists! (expected 1 item equipped)"
        )

        # Verify result: One success, one failure
        results = [fut1.result(), fut2.result()]
        successes = [r for r in results if r[0] is True]
        failures = [r for r in results if r[0] is False]

        self.assertEqual(len(successes), 1)
        self.assertEqual(len(failures), 1)
        self.assertIn("Equipment slot update conflict", failures[0][1])


if __name__ == "__main__":
    unittest.main()
