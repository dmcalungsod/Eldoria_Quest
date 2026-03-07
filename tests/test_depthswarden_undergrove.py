import unittest

from game_systems.data.adventure_locations import load_locations


class TestDepthswardenUndergrove(unittest.TestCase):
    def test_undergrove_exists(self):
        LOCATIONS = load_locations()
        self.assertIn("the_undergrove", LOCATIONS)
        loc = LOCATIONS["the_undergrove"]
        self.assertEqual(loc["min_rank"], "B")
        self.assertEqual(loc["level_req"], 25)


    def test_spore_gatherers_faction_exists(self):
        import json
        from pathlib import Path
        data_path = Path("game_systems/data/factions.json")
        with open(data_path, encoding="utf-8") as f:
            FACTIONS = json.load(f)
        self.assertIn("spore_gatherers", FACTIONS)
        faction = FACTIONS["spore_gatherers"]
        self.assertEqual(faction["name"], "The Spore-Gatherers")
        self.assertIn("4", faction["ranks"])
        self.assertEqual(faction["ranks"]["4"]["title"], "Spore-Lord")

if __name__ == "__main__":
    unittest.main()
