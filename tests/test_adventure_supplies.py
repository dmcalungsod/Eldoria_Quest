import os
import sys
import unittest
from unittest.mock import MagicMock

# Mock dependencies
sys.modules["pymongo"] = MagicMock()
sys.modules["pymongo.errors"] = MagicMock()
sys.modules["discord"] = MagicMock()
sys.modules["discord.ext"] = MagicMock()

sys.path.append(os.getcwd())

from database.database_manager import DatabaseManager
from game_systems.adventure.adventure_session import AdventureSession


class TestAdventureSupplies(unittest.TestCase):
    def setUp(self):
        self.db = MagicMock(spec=DatabaseManager)
        # Mock bundle fetch
        self.db.get_combat_context_bundle.return_value = {
            "stats": {},
            "buffs": [],
            "player": {"current_hp": 100, "current_mp": 100},
            "skills": [],
        }
        self.db.get_active_boosts.return_value = []

    def test_no_supplies_fatigue(self):
        """Verify standard fatigue without supplies."""
        row_data = {
            "location_id": "test",
            "active": 1,
            "logs": "[]",
            "loot_collected": "{}",
            "active_monster_json": None,
            "supplies": {},
        }
        session = AdventureSession(self.db, None, None, 12345, row_data=row_data)

        # 20 steps (4 over threshold of 16)
        # Bonus = (4/4) * 0.05 = 0.05. Total 1.05
        session.steps_completed = 20
        mult = session._calculate_fatigue_multiplier()
        self.assertAlmostEqual(mult, 1.05, places=4)

    def test_hardtack_fatigue(self):
        """Verify hardtack reduces fatigue buildup."""
        row_data = {
            "location_id": "test",
            "active": 1,
            "logs": "[]",
            "loot_collected": "{}",
            "active_monster_json": None,
            "supplies": {"hardtack": 1},
        }
        session = AdventureSession(self.db, None, None, 12345, row_data=row_data)

        # 20 steps
        # Bonus = 0.05 * 0.8 = 0.04. Total 1.04
        session.steps_completed = 20
        mult = session._calculate_fatigue_multiplier()
        self.assertAlmostEqual(mult, 1.04, places=4)

    def test_load_supplies(self):
        """Verify supplies are loaded from row_data."""
        supplies = {"torch": 1, "food": 5}
        row_data = {
            "location_id": "test",
            "active": 1,
            "logs": "[]",
            "loot_collected": "{}",
            "active_monster_json": None,
            "supplies": supplies,
        }
        session = AdventureSession(self.db, None, None, 12345, row_data=row_data)
        self.assertEqual(session.supplies, supplies)


if __name__ == "__main__":
    unittest.main()
