import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add repo root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock dependencies
try:
    import pymongo  # noqa: F401
except ImportError:
    mock_pymongo = MagicMock()
    mock_pymongo.errors = MagicMock()
    sys.modules["pymongo"] = mock_pymongo
    sys.modules["pymongo.errors"] = mock_pymongo.errors
    if not isinstance(mock_pymongo.errors.DuplicateKeyError, type):
        mock_pymongo.errors.DuplicateKeyError = type("DuplicateKeyError", (Exception,), {})

try:
    import discord  # noqa: F401
except ImportError:
    mock_discord = MagicMock()
    mock_discord.ext = MagicMock()
    sys.modules["discord"] = mock_discord
    sys.modules["discord.ext"] = mock_discord.ext

from database.database_manager import DatabaseManager
from game_systems.adventure.adventure_session import AdventureSession
from game_systems.core.world_time import TimePhase, Weather


class TestAdventureSuppliesExtended(unittest.TestCase):
    def setUp(self):
        self.db = MagicMock(spec=DatabaseManager)
        # Mock bundle
        self.context_mock = {
            "stats": {},
            "buffs": [],
            "player": {"current_hp": 100, "current_mp": 100, "level": 1, "class_id": 1},
            "skills": [],
            "player_stats": MagicMock(max_hp=100, max_mp=100, agility=10, luck=10),
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

    def test_auto_potion_usage(self):
        """Verify Auto-Potion triggers at low HP and consumes supply."""
        row_data = {
            "location_id": "test_loc",
            "active": 1,
            "logs": "[]",
            "loot_collected": "{}",
            "active_monster_json": None,
            "supplies": {"hp_potion_1": 2},
        }
        session = AdventureSession(self.db, None, None, 12345, row_data=row_data)

        # Mock HP to be critical (20/100 = 20% < 30%)
        self.context_mock["vitals"]["current_hp"] = 20

        # Manually trigger the helper (since simulate_step is complex to mock fully)
        # But we want to test that _try_auto_potion works.
        log = session._try_auto_potion(self.context_mock, max_hp=100)

        # Verify Usage
        self.assertIsNotNone(log)
        self.assertIn("Used Dewfall Tonic", log)
        self.assertEqual(session.supplies["hp_potion_1"], 1)
        # Check HP update (50 heal)
        self.assertEqual(self.context_mock["vitals"]["current_hp"], 70)

    def test_auto_potion_depletion(self):
        """Verify potion is removed when count hits 0."""
        row_data = {
            "location_id": "test_loc",
            "active": 1,
            "logs": "[]",
            "loot_collected": "{}",
            "active_monster_json": None,
            "supplies": {"hp_potion_1": 1},
        }
        session = AdventureSession(self.db, None, None, 12345, row_data=row_data)
        self.context_mock["vitals"]["current_hp"] = 20

        session._try_auto_potion(self.context_mock, max_hp=100)

        self.assertNotIn("hp_potion_1", session.supplies)

    def test_explorer_kit_bonus(self):
        """Verify Explorer's Kit increases wild gathering yield."""
        row_data = {
            "location_id": "forest_outskirts",
            "active": 1,
            "logs": "[]",
            "loot_collected": "{}",
            "active_monster_json": None,
            "supplies": {"explorer_kit": 1},
        }
        mock_quest = MagicMock()
        mock_quest.get_player_quests.return_value = [] # No active quests

        session = AdventureSession(self.db, mock_quest, None, 12345, row_data=row_data)

        with patch("game_systems.adventure.adventure_session.WorldTime") as MockTime:
            MockTime.get_current_weather.return_value = Weather.CLEAR
            MockTime.get_current_phase.return_value = TimePhase.DAY

            # Mock random.randint:
            # 1. simulate_step combat check: 10 (Pass <= 40 -> Non-Combat)
            # 2. resolve_non_combat regen check: 75 (Fail > 70 -> Wild Gather)
            # 3. _perform_wild_gathering success check: 10 (Pass <= 35 -> Loot)
            with patch("random.randint", side_effect=[10, 75, 10]):
                # Mock choice
                with patch("random.choices", return_value=["medicinal_herb"]):
                    with patch("random.random", return_value=0.5): # No extra variance
                        with patch.object(session, "_fetch_session_context", return_value=self.context_mock):
                            result = session.simulate_step(context_bundle=None)

                            loot = session.loot
                            # Base yield 1 (luck 10/25 = 0 bonus).
                            # Kit bonus +1. Total 2.
                            self.assertEqual(loot.get("medicinal_herb"), 2)

                            logs = "".join(result["sequence"][0])
                            self.assertIn("Kit Bonus", logs)

    def test_explorer_kit_no_effect_without_supply(self):
        """Verify wild gathering yield is normal without kit."""
        row_data = {
            "location_id": "forest_outskirts",
            "active": 1,
            "logs": "[]",
            "loot_collected": "{}",
            "active_monster_json": None,
            "supplies": {},
        }
        mock_quest = MagicMock()
        mock_quest.get_player_quests.return_value = []

        session = AdventureSession(self.db, mock_quest, None, 12345, row_data=row_data)

        with patch("game_systems.adventure.adventure_session.WorldTime") as MockTime:
            MockTime.get_current_weather.return_value = Weather.CLEAR
            MockTime.get_current_phase.return_value = TimePhase.DAY

            # Mock random.randint: 10 (Non-Combat), 75 (Wild Gather), 10 (Success)
            with patch("random.randint", side_effect=[10, 75, 10]):
                with patch("random.choices", return_value=["medicinal_herb"]):
                    with patch("random.random", return_value=0.5):
                        with patch.object(session, "_fetch_session_context", return_value=self.context_mock):
                            result = session.simulate_step(context_bundle=None)

                            loot = session.loot
                            # Base yield 1
                            self.assertEqual(loot.get("medicinal_herb"), 1)

if __name__ == "__main__":
    unittest.main()
