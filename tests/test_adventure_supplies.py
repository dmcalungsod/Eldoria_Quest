import os
import sys
import unittest
from unittest.mock import MagicMock, patch

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
            "stats": {"HP": 100, "MP": 100},
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
        # Call with default 0.0 bonus
        mult = session._calculate_fatigue_multiplier(0.0)
        self.assertAlmostEqual(mult, 1.05, places=4)

    def test_hardtack_fatigue_calculation(self):
        """Verify passing reduction bonus works correctly."""
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

        # Manually pass 0.2 bonus (simulating hardtack)
        mult = session._calculate_fatigue_multiplier(0.2)
        self.assertAlmostEqual(mult, 1.04, places=4)

    @patch("game_systems.adventure.adventure_session.WorldEventSystem")
    @patch("game_systems.adventure.adventure_session.CONSUMABLES", {
        "hardtack": {"type": "supply", "effect": {"fatigue_reduction": 0.2}},
        "pitch_torch": {"type": "supply", "effect": {"ambush_reduction": 0.5}}
    })
    def test_supply_context_integration(self, MockEventSystem):
        """Verify _fetch_session_context correctly merges supply effects."""
        # Mock event system to avoid time/DB calls
        mock_es = MockEventSystem.return_value
        mock_es.get_current_event.return_value = None

        row_data = {
            "location_id": "test",
            "active": 1,
            "logs": "[]",
            "loot_collected": "{}",
            "active_monster_json": None,
            "supplies": {"hardtack": 1, "pitch_torch": 1},
        }
        session = AdventureSession(self.db, None, None, 12345, row_data=row_data)

        # Ensure context bundle returns mock data
        self.db.get_combat_context_bundle.return_value = {
            "stats": {"HP": 100, "MP": 100},
            "buffs": [],
            "player": {"current_hp": 100, "current_mp": 100},
            "skills": [],
        }

        context = session._fetch_session_context()
        self.assertIsNotNone(context)

        boosts = context["active_boosts"]
        self.assertIn("fatigue_reduction", boosts)
        self.assertAlmostEqual(boosts["fatigue_reduction"], 0.2)
        self.assertIn("ambush_reduction", boosts)
        self.assertAlmostEqual(boosts["ambush_reduction"], 0.5)

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
