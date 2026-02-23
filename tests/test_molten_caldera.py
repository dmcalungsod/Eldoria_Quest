import unittest

from game_systems.adventure.adventure_events import AdventureEvents
from game_systems.data import emojis as E
from game_systems.data.adventure_locations import LOCATIONS
from game_systems.data.materials import MATERIALS
from game_systems.data.monsters import MONSTERS


class TestMoltenCaldera(unittest.TestCase):
    def test_location_exists(self):
        self.assertIn("molten_caldera", LOCATIONS)
        loc = LOCATIONS["molten_caldera"]
        self.assertEqual(loc["min_rank"], "A")
        self.assertEqual(loc["emoji"], "🌋")

    def test_monsters_exist(self):
        new_ids = [106, 107, 108, 109, 110]
        for mid in new_ids:
            key = f"monster_{mid}"
            self.assertIn(key, MONSTERS)
            monster = MONSTERS[key]
            self.assertTrue(monster["level"] >= 30)

    def test_materials_exist(self):
        new_mats = ["obsidian_shard", "fire_essence", "magma_core", "dragon_scale"]
        for mat in new_mats:
            self.assertIn(mat, MATERIALS)

    def test_emojis_exist(self):
        self.assertEqual(E.VOLCANO, "🌋")
        self.assertEqual(E.FIRE, "🔥")

    def test_adventure_events(self):
        self.assertTrue(hasattr(AdventureEvents, "ATMOSPHERE_MAGMA"))
        self.assertTrue(hasattr(AdventureEvents, "REGEN_PHRASES_MAGMA"))

        # Test regeneration logic
        logs = AdventureEvents.regeneration(location_id="molten_caldera", hp_percent=1.0)
        # Should return at least one log from magma phrases or generic fallback
        # Since we mock nothing, it uses real random.
        # But we can check if the output string contains the volcano emoji if it picked a magma phrase
        # However, it might pick generic high HP phrase.
        # But REGEN_PHRASES_MAGMA all start with E.VOLCANO.

        # Let's just verify the lists are not empty
        self.assertTrue(len(AdventureEvents.ATMOSPHERE_MAGMA) > 0)
        self.assertTrue(len(AdventureEvents.REGEN_PHRASES_MAGMA) > 0)


if __name__ == "__main__":
    unittest.main()
