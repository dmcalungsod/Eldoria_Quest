import sys
from unittest.mock import MagicMock

# Mock pymongo before importing any app modules
try:
    import pymongo  # noqa: F401
except ImportError:
    mock_pymongo = MagicMock()
    sys.modules["pymongo"] = mock_pymongo

import unittest
from unittest.mock import patch

from game_systems.adventure.combat_handler import CombatHandler
from game_systems.data.monsters import MONSTERS


class TestDayNightCycle(unittest.TestCase):
    def setUp(self):
        self.mock_db = MagicMock()
        self.handler = CombatHandler(self.mock_db, discord_id=123456789)

        self.mock_location = {
            "name": "Test Forest",
            "monsters": [("monster_001", 100)],
            "night_monsters": [("monster_003", 100)],
            "conditional_monsters": [],
        }

        self.original_monsters = MONSTERS.copy()
        MONSTERS["monster_001"] = {
            "name": "Day Slime",
            "level": 1,
            "tier": "Normal",
            "hp": 10,
            "atk": 1,
            "def": 1,
            "xp": 10,
            "drops": [],
            "skills": [],
        }
        MONSTERS["monster_003"] = {
            "name": "Night Goblin",
            "level": 2,
            "tier": "Normal",
            "hp": 20,
            "atk": 2,
            "def": 1,
            "xp": 20,
            "drops": [],
            "skills": [],
        }

    def tearDown(self):
        MONSTERS.clear()
        MONSTERS.update(self.original_monsters)

    def test_day_encounter(self):
        # Patch WorldTime in combat_handler
        with patch("game_systems.adventure.combat_handler.WorldTime") as MockWorldTime:
            MockWorldTime.is_night.return_value = False
            MockWorldTime.get_phase_flavor.return_value = "☀️ **Day**"

            monster, phrase = self.handler.initiate_combat(self.mock_location)

            if monster:
                self.assertEqual(monster["name"], "Day Slime")
            else:
                self.fail("No monster returned")

            self.assertIn("Day", phrase)

    def test_night_encounter(self):
        with patch("game_systems.adventure.combat_handler.WorldTime") as MockWorldTime:
            MockWorldTime.is_night.return_value = True
            MockWorldTime.get_phase_flavor.return_value = "🌑 **Night**"

            monster, phrase = self.handler.initiate_combat(self.mock_location)

            if monster:
                self.assertEqual(monster["name"], "Night Goblin")
            else:
                self.fail("No monster returned")

            self.assertIn("Night", phrase)

    def test_night_encounter_fallback(self):
        location_no_night = {"name": "Sunny Plains", "monsters": [("monster_001", 100)], "conditional_monsters": []}

        with patch("game_systems.adventure.combat_handler.WorldTime") as MockWorldTime:
            MockWorldTime.is_night.return_value = True
            MockWorldTime.get_phase_flavor.return_value = "🌑 **Night**"

            monster, phrase = self.handler.initiate_combat(location_no_night)

            if monster:
                self.assertEqual(monster["name"], "Day Slime")
            else:
                self.fail("No monster returned")

            self.assertIn("Night", phrase)


if __name__ == "__main__":
    unittest.main()
