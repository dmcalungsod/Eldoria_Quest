import os
import sys
import unittest

# Add repo root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game_systems.data.monsters import MONSTERS
from game_systems.monsters.monster_skills import MONSTER_SKILLS


class TestMonsterData(unittest.TestCase):
    def test_monsters_loaded(self):
        """Test that MONSTERS dictionary is populated."""
        self.assertIsInstance(MONSTERS, dict)
        self.assertGreater(len(MONSTERS), 0)

    def test_monster_structure(self):
        """Test that a sample monster has the expected fields."""
        # Grab any monster, e.g., monster_001
        monster = MONSTERS.get("monster_001")
        if not monster:
            self.skipTest("monster_001 not found")

        required_fields = ["id", "name", "level", "hp", "atk", "def", "xp", "drops", "skills"]
        for field in required_fields:
            self.assertIn(field, monster)

    def test_skills_rehydration(self):
        """Test that skills are converted from keys to objects."""
        monster = MONSTERS.get("monster_001")
        if not monster:
            self.skipTest("monster_001 not found")

        skills = monster["skills"]
        self.assertIsInstance(skills, list)
        if len(skills) > 0:
            skill = skills[0]
            self.assertIsInstance(skill, dict)
            self.assertIn("key_id", skill)
            self.assertIn("name", skill)

            # verify it matches the source
            key_id = skill["key_id"]
            self.assertEqual(skill, MONSTER_SKILLS[key_id])

    def test_drops_conversion(self):
        """Test that drops are converted to tuples."""
        monster = MONSTERS.get("monster_001")
        if not monster:
            self.skipTest("monster_001 not found")

        drops = monster["drops"]
        self.assertIsInstance(drops, list)
        if len(drops) > 0:
            drop = drops[0]
            self.assertIsInstance(drop, tuple)
            self.assertEqual(len(drop), 2)


if __name__ == "__main__":
    unittest.main()
