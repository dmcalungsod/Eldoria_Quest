import json
import os
import unittest

from game_systems.data.consumables import CONSUMABLES
from game_systems.data.materials import MATERIALS
from game_systems.data.monsters import MONSTERS


class TestSunkenGrottoQuests(unittest.TestCase):
    def setUp(self):
        # Load quests.json
        quests_path = os.path.join(os.path.dirname(__file__), "../game_systems/data/quests.json")
        with open(quests_path, encoding="utf-8") as f:
            self.quests = json.load(f)

        # Map Quest ID to Quest Object
        self.quest_map = {q["id"]: q for q in self.quests}

        # Valid Monster Names
        self.valid_monster_names = {m["name"] for m in MONSTERS.values()}

        # Valid Item Names (Consumables + Materials)
        self.valid_item_names = {c["name"] for c in CONSUMABLES.values()}
        self.valid_item_names.update({m["name"] for m in MATERIALS.values()})

    def test_new_quests_exist(self):
        """Verify that Quests 56-60 exist."""
        for q_id in range(56, 61):
            self.assertIn(q_id, self.quest_map, f"Quest ID {q_id} missing from quests.json")

    def test_quest_details(self):
        """Verify details for Sunken Grotto quests."""
        expected_quests = {
            56: {
                "title": "Tide of Stone",
                "tier": "C",
                "location": "The Sunken Grotto",
                "target": "Coral Golem",
                "count": 5
            },
            57: {
                "title": "Lurkers in the Deep",
                "tier": "C",
                "location": "The Sunken Grotto",
                "target": "Abyssal Eel",
                "count": 5
            },
            58: {
                "title": "Siren's Call",
                "tier": "C",
                "location": "The Sunken Grotto",
                "target": "Tide Siren",
                "count": 5
            },
            59: {
                "title": "Crushing Depths",
                "tier": "C",
                "location": "The Sunken Grotto",
                "target": "Deep Crawler",
                "count": 3
            },
            60: {
                "title": "The Leviathan's Wake",
                "tier": "C",
                "location": "The Sunken Grotto",
                "target": "Leviathan",
                "count": 1
            }
        }

        for q_id, details in expected_quests.items():
            if q_id not in self.quest_map:
                continue # Skip if not implemented yet (will fail in test_new_quests_exist)

            quest = self.quest_map[q_id]
            self.assertEqual(quest["title"], details["title"])
            self.assertEqual(quest["tier"], details["tier"])
            self.assertEqual(quest["location"], details["location"])

            # Verify Objective
            objectives = quest["objectives"]
            self.assertIn("defeat", objectives)
            targets = objectives["defeat"]
            self.assertIn(details["target"], targets)
            self.assertEqual(targets[details["target"]], details["count"])

            # Verify Target Name Validity
            self.assertIn(details["target"], self.valid_monster_names, f"Monster {details['target']} not defined in MONSTERS")

            # Verify Reward Item Validity (if present)
            if "item" in quest["rewards"]:
                item_name = quest["rewards"]["item"]
                self.assertIn(item_name, self.valid_item_names, f"Reward item {item_name} not found in CONSUMABLES or MATERIALS")

if __name__ == "__main__":
    unittest.main()
