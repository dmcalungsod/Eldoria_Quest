import os
import sys
import unittest

# Mock pymongo before importing game systems
from unittest.mock import MagicMock

sys.modules["pymongo"] = MagicMock()
sys.modules["pymongo.collection"] = MagicMock()
sys.modules["pymongo.database"] = MagicMock()

# Add repo root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from game_systems.data.adventure_locations import LOCATIONS  # noqa: E402
from game_systems.data.materials import MATERIALS  # noqa: E402
from game_systems.data.monsters import MONSTERS  # noqa: E402
from game_systems.monsters.monster_skills import MONSTER_SKILLS  # noqa: E402


class TestDepthsWardenContent(unittest.TestCase):
    def test_void_sanctum_exists(self):
        """Verify 'void_sanctum' is in LOCATIONS."""
        self.assertIn("void_sanctum", LOCATIONS)
        loc = LOCATIONS["void_sanctum"]
        self.assertEqual(loc["min_rank"], "S")
        self.assertEqual(loc["level_req"], 40)
        self.assertIn("monster_116", [m[0] for m in loc["monsters"]])

    def test_new_monsters_exist(self):
        """Verify monsters 116-120 exist and are valid."""
        for mid in range(116, 121):
            key = f"monster_{mid}"
            self.assertIn(key, MONSTERS, f"Monster {mid} missing")
            monster = MONSTERS[key]
            self.assertTrue(monster["level"] >= 41, f"Monster {mid} level too low")
            self.assertTrue(len(monster["skills"]) > 0, f"Monster {mid} has no skills")

    def test_new_materials_exist(self):
        """Verify new Void materials exist."""
        new_mats = ["void_dust", "abyssal_shackle", "entropy_crystal", "null_stone", "void_heart"]
        for mat in new_mats:
            self.assertIn(mat, MATERIALS, f"Material {mat} missing")

    def test_monster_skills(self):
        """Verify new skills are in MONSTER_SKILLS."""
        new_skills = ["void_slash", "entropy_wave", "annihilate"]
        for skill in new_skills:
            self.assertIn(skill, MONSTER_SKILLS)


if __name__ == "__main__":
    unittest.main()
