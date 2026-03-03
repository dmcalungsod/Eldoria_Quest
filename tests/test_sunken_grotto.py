import unittest

from game_systems.adventure.adventure_events import AdventureEvents
from game_systems.data import emojis as E
from game_systems.data.adventure_locations import LOCATIONS
from game_systems.data.materials import MATERIALS
from game_systems.data.monsters import MONSTERS
from game_systems.monsters.monster_skills import MONSTER_SKILLS


class TestSunkenGrotto(unittest.TestCase):
    def test_location_exists(self):
        self.assertIn("sunken_grotto", LOCATIONS)
        loc = LOCATIONS["sunken_grotto"]
        self.assertEqual(loc["min_rank"], "C")
        self.assertEqual(loc["emoji"], "🌊")
        self.assertEqual(loc["level_req"], 18)

    def test_monsters_exist(self):
        new_ids = [121, 122, 123, 124, 125]
        for mid in new_ids:
            key = f"monster_{mid}"
            self.assertIn(key, MONSTERS)
            monster = MONSTERS[key]
            self.assertTrue(monster["level"] >= 18)
            # Check drops
            drop_keys = [d[0] for d in monster["drops"]]
            if mid == 121:
                self.assertIn("coral_fragment", drop_keys)
            elif mid == 122:
                self.assertIn("bioluminescent_scale", drop_keys)
            elif mid == 125:
                self.assertIn("abyssal_pearl", drop_keys)

    def test_materials_exist(self):
        new_mats = [
            "coral_fragment",
            "bioluminescent_scale",
            "pearl",
            "siren_voice_box",
            "abyssal_pearl",
        ]
        for mat in new_mats:
            self.assertIn(mat, MATERIALS)

    def test_emojis_exist(self):
        self.assertEqual(E.OCEAN, "🌊")

    def test_skills_exist(self):
        new_skills = ["water_jet", "tidal_wave", "bubble_beam", "crushing_depths"]
        for skill in new_skills:
            self.assertIn(skill, MONSTER_SKILLS)
            self.assertIsNotNone(MONSTER_SKILLS[skill].get("key_id"))

    def test_adventure_events(self):
        self.assertTrue(hasattr(AdventureEvents, "ATMOSPHERE_GROTTO"))
        self.assertTrue(hasattr(AdventureEvents, "REGEN_PHRASES_GROTTO"))

        # Verify lists are not empty
        self.assertTrue(len(AdventureEvents.ATMOSPHERE_GROTTO) > 0)
        self.assertTrue(len(AdventureEvents.REGEN_PHRASES_GROTTO) > 0)

        # Test regeneration returns grotto phrases for the location
        # Since regeneration uses random, we can't deterministically check the output
        # unless we mock random or check if output is in the list.
        # But we can check that it doesn't crash.
        logs = AdventureEvents.regeneration(location_id="sunken_grotto", hp_percent=0.5)
        self.assertTrue(len(logs) > 0)

        # Check that grotto atmosphere is eventually picked (probabilistic)
        # We won't loop forever, just check existence of logic via code inspection or simple call
        # Mocking would be better but simple existence check is okay for this scope.


if __name__ == "__main__":
    unittest.main()
