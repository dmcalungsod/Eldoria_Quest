import unittest
import sys
import os

# Add repo root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from game_systems.adventure.adventure_events import AdventureEvents
from game_systems.data import emojis as E
from game_systems.data.adventure_locations import LOCATIONS
from game_systems.data.materials import MATERIALS
from game_systems.data.monsters import MONSTERS
from game_systems.monsters.monster_skills import MONSTER_SKILLS

class TestClockworkHalls(unittest.TestCase):
    def test_location_exists(self):
        self.assertIn("clockwork_halls", LOCATIONS)
        loc = LOCATIONS["clockwork_halls"]
        self.assertEqual(loc["min_rank"], "B")
        self.assertEqual(loc["emoji"], "⚙️")
        self.assertEqual(loc["level_req"], 22)

    def test_monsters_exist(self):
        new_ids = [126, 127, 128, 129, 130]
        for mid in new_ids:
            key = f"monster_{mid}"
            self.assertIn(key, MONSTERS)
            monster = MONSTERS[key]
            self.assertTrue(monster["level"] >= 22)
            # Check drops
            drop_keys = [d[0] for d in monster["drops"]]
            if mid == 126:
                self.assertIn("brass_gear", drop_keys)
            elif mid == 127:
                self.assertIn("copper_wire", drop_keys)
            elif mid == 130:
                self.assertIn("clockwork_heart", drop_keys)

    def test_materials_exist(self):
        new_mats = ["brass_gear", "copper_wire", "spring_coil", "steam_core", "clockwork_heart"]
        for mat in new_mats:
            self.assertIn(mat, MATERIALS)

    def test_emojis_exist(self):
        self.assertEqual(E.GEAR, "⚙️")

    def test_skills_exist(self):
        new_skills = ["steam_vent"]
        for skill in new_skills:
            self.assertIn(skill, MONSTER_SKILLS)
            self.assertIsNotNone(MONSTER_SKILLS[skill].get("key_id"))

    def test_adventure_events(self):
        self.assertTrue(hasattr(AdventureEvents, "ATMOSPHERE_CLOCKWORK"))
        self.assertTrue(hasattr(AdventureEvents, "REGEN_PHRASES_CLOCKWORK"))

        # Verify lists are not empty
        self.assertTrue(len(AdventureEvents.ATMOSPHERE_CLOCKWORK) > 0)
        self.assertTrue(len(AdventureEvents.REGEN_PHRASES_CLOCKWORK) > 0)

        logs = AdventureEvents.regeneration(location_id="clockwork_halls", hp_percent=0.5)
        self.assertTrue(len(logs) > 0)

        # Test that we can possibly get a clockwork phrase (mocking random would be better but this is a sanity check)
        # We check if the regeneration method runs without error for the new location

if __name__ == "__main__":
    unittest.main()
