import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add repo root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock dependencies before import (consistent with test_adventure_day_night.py)
# We use a simple import check which is robust against conftest.py mocking.
# If pymongo is already mocked by conftest, the import will succeed (returning the mock).
# If it's not installed, ImportError is raised, and we mock it ourselves.
try:
    import pymongo  # noqa: F401
except ImportError:
    mock_pymongo = MagicMock()
    mock_pymongo.errors = MagicMock()
    sys.modules["pymongo"] = mock_pymongo
    sys.modules["pymongo.errors"] = mock_pymongo.errors
    # Ensure DuplicateKeyError is a real exception (handled by conftest usually, but safe here)
    if not isinstance(mock_pymongo.errors.DuplicateKeyError, type):
        mock_pymongo.errors.DuplicateKeyError = type("DuplicateKeyError", (Exception,), {})

try:
    import discord  # noqa: F401
except ImportError:
    mock_discord = MagicMock()
    mock_discord.ext = MagicMock()
    sys.modules["discord"] = mock_discord
    sys.modules["discord.ext"] = mock_discord.ext

from database.database_manager import DatabaseManager  # noqa: E402
from game_systems.adventure.adventure_session import AdventureSession  # noqa: E402
from game_systems.core.world_time import TimePhase, Weather  # noqa: E402


class TestAdventureSupplies(unittest.TestCase):
    def setUp(self):
        self.db = MagicMock(spec=DatabaseManager)
        # Mock bundle fetch with default valid structure
        self.context_mock = {
            "stats": {},
            "buffs": [],
            "player": {"current_hp": 100, "current_mp": 100, "level": 1, "class_id": 1},
            "skills": [],
            "player_stats": MagicMock(max_hp=100, max_mp=100, agility=10),
            "stats_dict": {"HP": 100, "MP": 100},
            "vitals": {"current_hp": 100, "current_mp": 100},
            "player_row": {"level": 1, "class_id": 1, "current_hp": 100, "current_mp": 100},
            "active_boosts": {},
            "event_type": None,
        }
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

        # 300 steps (60 over threshold of 240)
        # Bonus = (60/60) * 0.05 = 0.05. Total 1.05
        session.steps_completed = 300
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

        # 300 steps
        # Bonus = 0.05 * 0.8 = 0.04. Total 1.04
        session.steps_completed = 300
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

    def test_pitch_torch_ambush_reduction(self):
        """
        Verify Pitch Torch reduces ambush chance at night.
        Base Night Ambush Chance: 0.20
        With Pitch Torch: 0.20 * 0.5 = 0.10
        """
        # Setup session with Pitch Torch
        row_data = {
            "location_id": "forest_outskirts",
            "active": 1,
            "logs": "[]",
            "loot_collected": "{}",
            "active_monster_json": None,
            "supplies": {"pitch_torch": 1},
        }

        # Mock dependencies
        mock_quest = MagicMock()
        mock_inv = MagicMock()

        session = AdventureSession(self.db, mock_quest, mock_inv, 12345, row_data=row_data)

        monster_data = {"name": "Test Goblin", "ATK": 20, "level": 1, "tier": "Normal"}

        # Use patches to control WorldTime and random
        with patch("game_systems.adventure.adventure_session.WorldTime") as MockTime:
            MockTime.get_current_weather.return_value = Weather.CLEAR
            MockTime.get_current_phase.return_value = TimePhase.NIGHT
            MockTime.get_weather_flavor.return_value = "Clear Night"

            with patch.object(session, "_fetch_session_context", return_value=self.context_mock):
                # Force combat trigger (roll 100 > threshold)
                with patch("random.randint", return_value=100):
                    # Mock initiate_combat to return a monster
                    session.combat.initiate_combat = MagicMock(return_value=(monster_data, "A wild goblin appears!"))

                    # --- CRITICAL TEST: AMBUSH CHANCE ---
                    # We simulate a roll of 0.15.
                    # Without Pitch Torch (0.20), 0.15 < 0.20 -> Ambush!
                    # With Pitch Torch (0.10), 0.15 > 0.10 -> No Ambush!
                    with patch("random.random", return_value=0.15):
                        result = session.simulate_step(context_bundle=None)

                        logs = "".join(result["sequence"][0])

                        # Expectation: NO Ambush, because 0.15 > 0.10
                        self.assertNotIn("AMBUSH!", logs)
                        self.assertEqual(self.context_mock["vitals"]["current_hp"], 100)

    def test_night_ambush_without_torch(self):
        """
        Verify Ambush DOES happen without Pitch Torch for the same roll.
        """
        row_data = {
            "location_id": "forest_outskirts",
            "active": 1,
            "logs": "[]",
            "loot_collected": "{}",
            "active_monster_json": None,
            "supplies": {},  # No Torch
        }

        mock_quest = MagicMock()
        mock_inv = MagicMock()
        session = AdventureSession(self.db, mock_quest, mock_inv, 12345, row_data=row_data)

        monster_data = {"name": "Test Goblin", "ATK": 20, "level": 1, "tier": "Normal"}

        with patch("game_systems.adventure.adventure_session.WorldTime") as MockTime:
            MockTime.get_current_weather.return_value = Weather.CLEAR
            MockTime.get_current_phase.return_value = TimePhase.NIGHT
            MockTime.get_weather_flavor.return_value = "Clear Night"

            with patch.object(session, "_fetch_session_context", return_value=self.context_mock):
                with patch("random.randint", return_value=100):
                    session.combat.initiate_combat = MagicMock(return_value=(monster_data, "A wild goblin appears!"))

                    # Same roll of 0.15
                    # Without Torch (0.20 threshold): 0.15 < 0.20 -> Ambush!
                    with patch("random.random", return_value=0.15):
                        result = session.simulate_step(context_bundle=None)

                        logs = "".join(result["sequence"][0])
                        self.assertIn("AMBUSH!", logs)

                        # Damage verification (20 * 0.8 = 16)
                        # We just check HP dropped, exact calc handled by combat logic
                        self.assertTrue(self.context_mock["vitals"]["current_hp"] < 100)


if __name__ == "__main__":
    unittest.main()
