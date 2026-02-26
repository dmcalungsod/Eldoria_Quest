import unittest
import json
import sys
import os
from pathlib import Path

# Add root to path
sys.path.append(os.getcwd())

from game_systems.data.consumables import CONSUMABLES
from game_systems.data.materials import MATERIALS

class TestQuestJsonIntegrity(unittest.TestCase):
    def setUp(self):
        self.quest_path = Path("game_systems/data/quests.json")
        with open(self.quest_path, "r", encoding="utf-8") as f:
            self.quests = json.load(f)

        self.quest_ids = {q["id"] for q in self.quests}

    def test_unique_ids(self):
        """Ensure all quest IDs are unique."""
        ids = [q["id"] for q in self.quests]
        self.assertEqual(len(ids), len(set(ids)), "Duplicate Quest IDs found!")

    def test_prerequisites_exist(self):
        """Ensure all prerequisites point to valid quest IDs."""
        for quest in self.quests:
            prereqs = quest.get("prerequisites", [])
            if isinstance(prereqs, int):
                prereqs = [prereqs]

            for pid in prereqs:
                self.assertIn(pid, self.quest_ids, f"Quest {quest['id']} has invalid prerequisite ID {pid}")

    def test_reward_items_exist(self):
        """Ensure all item rewards exist in CONSUMABLES or MATERIALS."""
        for quest in self.quests:
            rewards = quest.get("rewards", {})
            item_name = rewards.get("item")

            if item_name:
                found = False
                # Check Consumables
                for c in CONSUMABLES.values():
                    if c["name"] == item_name:
                        found = True
                        break

                if not found:
                    # Check Materials
                    for m in MATERIALS.values():
                        if m["name"] == item_name:
                            found = True
                            break

                self.assertTrue(found, f"Quest {quest['id']} rewards unknown item: '{item_name}'")

    def test_frozen_echo_chain(self):
        """Specific check for the new quest chain."""
        chain_ids = [70, 71, 72, 73]
        for qid in chain_ids:
            self.assertIn(qid, self.quest_ids, f"New Quest {qid} missing!")

        q70 = next(q for q in self.quests if q["id"] == 70)
        self.assertEqual(q70["title"], "The Frozen Echo: Signal")

        q73 = next(q for q in self.quests if q["id"] == 73)
        self.assertEqual(q73["rewards"]["item"], "Ice Core")
        # Verify Ice Core is a valid material
        found_ice_core = False
        for m in MATERIALS.values():
            if m["name"] == "Ice Core":
                found_ice_core = True
                break
        self.assertTrue(found_ice_core, "Ice Core not found in MATERIALS")

if __name__ == "__main__":
    unittest.main()
