import unittest
from unittest.mock import MagicMock, patch
import sys
import os
import datetime

# Add root to sys.path
sys.path.append(os.getcwd())

# Mock pymongo BEFORE importing DatabaseManager
mock_pymongo = MagicMock()
sys.modules["pymongo"] = mock_pymongo
sys.modules["pymongo.errors"] = MagicMock()

from game_systems.events.world_event_system import WorldEventSystem  # noqa: E402


class TestWorldEventSystem(unittest.TestCase):
    def setUp(self):
        self.mock_db = MagicMock()
        self.system = WorldEventSystem(self.mock_db)

    def test_start_event(self):
        self.system.start_event(WorldEventSystem.BLOOD_MOON, 24)
        self.mock_db.set_active_world_event.assert_called_once()
        args = self.mock_db.set_active_world_event.call_args[0]
        self.assertEqual(args[0], "blood_moon")

    def test_get_current_event_active(self):
        future_time = (
            datetime.datetime.now() + datetime.timedelta(hours=1)
        ).isoformat()
        self.mock_db.get_active_world_event.return_value = {
            "type": "blood_moon",
            "start_time": datetime.datetime.now().isoformat(),
            "end_time": future_time,
            "active": 1,
        }

        event = self.system.get_current_event()
        self.assertIsNotNone(event)
        self.assertEqual(event["type"], "blood_moon")
        self.assertIn("modifiers", event)
        self.assertEqual(event["modifiers"]["loot_boost"], 1.5)

    def test_get_current_event_expired(self):
        past_time = (datetime.datetime.now() - datetime.timedelta(hours=1)).isoformat()
        self.mock_db.get_active_world_event.return_value = {
            "type": "blood_moon",
            "start_time": (
                datetime.datetime.now() - datetime.timedelta(hours=2)
            ).isoformat(),
            "end_time": past_time,
            "active": 1,
        }

        event = self.system.get_current_event()
        self.assertIsNone(event)
        self.mock_db.end_active_world_event.assert_called_once()

    def test_get_modifiers(self):
        future_time = (
            datetime.datetime.now() + datetime.timedelta(hours=1)
        ).isoformat()
        self.mock_db.get_active_world_event.return_value = {
            "type": "celestial_convergence",
            "end_time": future_time,
            "active": 1,
        }
        mods = self.system.get_modifiers()
        self.assertEqual(mods["loot_boost"], 2.0)


if __name__ == "__main__":
    unittest.main()
