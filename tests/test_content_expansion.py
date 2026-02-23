import unittest

from game_systems.data.adventure_locations import LOCATIONS
from game_systems.data.monsters import MONSTERS
from game_systems.data.quest_data import ALL_QUESTS, QUESTS_C_TIER


class TestContentExpansion(unittest.TestCase):
    def test_shrouded_fen_location(self):
        """Verify 'The Shrouded Fen' is correctly defined."""
        self.assertIn("shrouded_fen", LOCATIONS, "shrouded_fen not found in LOCATIONS")
        fen = LOCATIONS["shrouded_fen"]
        self.assertEqual(fen["name"], "The Shrouded Fen")
        self.assertEqual(fen["min_rank"], "C")
        self.assertEqual(fen["level_req"], 15)

        # Verify monsters exist in MONSTERS
        for monster_key, _ in fen["monsters"]:
            self.assertIn(
                monster_key, MONSTERS, f"Monster {monster_key} not in MONSTERS"
            )

        if "conditional_monsters" in fen:
            for cm in fen["conditional_monsters"]:
                self.assertIn(
                    cm["monster_key"],
                    MONSTERS,
                    f"Conditional monster {cm['monster_key']} not in MONSTERS",
                )

    def test_c_tier_quests_loaded(self):
        """Verify C-Tier quests are loaded and structured correctly."""
        self.assertTrue(len(QUESTS_C_TIER) > 0, "QUESTS_C_TIER is empty")

        # Check if they are in ALL_QUESTS
        c_ids = [q["id"] for q in QUESTS_C_TIER]
        all_ids = [q["id"] for q in ALL_QUESTS]
        for qid in c_ids:
            self.assertIn(qid, all_ids, f"Quest ID {qid} not in ALL_QUESTS")

    def test_quest_monster_references(self):
        """Verify quest objectives reference valid monsters."""
        monster_names = {m["name"] for m in MONSTERS.values()}

        for q in QUESTS_C_TIER:
            title = q["title"]
            objectives = q["objectives"]

            if "defeat" in objectives:
                targets = objectives["defeat"]
                for target_name in targets:
                    self.assertIn(
                        target_name,
                        monster_names,
                        f"Quest '{title}' references unknown monster '{target_name}'",
                    )

    def test_quest_location_references(self):
        """Verify quests reference valid location names from LOCATIONS."""
        valid_location_names = {loc["name"] for loc in LOCATIONS.values()}

        for q in QUESTS_C_TIER:
            location = q["location"]
            self.assertIn(
                location,
                valid_location_names,
                f"Quest '{q['title']}' references unknown location '{location}'",
            )


if __name__ == "__main__":
    unittest.main()
