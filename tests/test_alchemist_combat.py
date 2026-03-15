import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add repo root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game_systems.combat.combat_engine import CombatEngine  # noqa: E402
from game_systems.player.player_stats import PlayerStats  # noqa: E402


class TestAlchemistCombatSkills(unittest.TestCase):
    def setUp(self):
        # Mock Player
        self.player = MagicMock()
        self.player.is_stunned = False
        self.player.is_silenced = False
        self.player.stats = PlayerStats(str_base=10, mag_base=10, dex_base=10)
        self.player.stats.get_total_stats_dict = MagicMock(
            return_value={"STR": 10, "MAG": 10, "DEX": 10, "HP": 100, "MP": 100}
        )
        self.player.hp_current = 100
        self.player.level = 5

        # Mock Monster
        self.monster = {
            "name": "Slime",
            "HP": 100,
            "max_hp": 100,
            "MP": 0,
            "ATK": 10,
            "DEF": 10,
            "AGI": 5,
            "DEX": 5,
            "debuffs": [],
        }

    def test_vitriol_bomb_def_reduction(self):
        """Test that Vitriol Bomb applies DEF reduction to the monster."""
        # Define Skill
        skill = {
            "key_id": "vitriol_bomb",
            "name": "Vitriol Bomb",
            "type": "Active",
            "mp_cost": 5,
            # Using DEF_percent as we suspect END_percent is ignored/wrong mapping
            "debuff": {"DEF_percent": -0.1, "duration": 3},
            "scaling_stat": "DEX",
        }

        # Setup Combat Engine
        engine = CombatEngine(
            player=self.player,
            monster=self.monster,
            player_skills=[skill],
            player_mp=50,
            player_class_id=6,
            action="skill:vitriol_bomb",
        )

        # Run Turn
        engine.run_combat_turn()

        # Check if debuff applied
        self.assertTrue(len(self.monster["debuffs"]) > 0, "No debuff applied")
        debuff = self.monster["debuffs"][0]
        self.assertEqual(debuff["name"], "Vitriol Bomb")
        self.assertIn("DEF_percent", debuff)
        self.assertEqual(debuff["DEF_percent"], -0.1)

        # Verify effective stats calculation reduces DEF
        eff_stats = engine._get_effective_monster_stats()
        # Base DEF 10, -10% -> 9
        self.assertEqual(eff_stats["DEF"], 9)

    def test_mutagenic_serum_self_damage(self):
        """Test that Mutagenic Serum (Buff) applies self-damage."""
        skill = {
            "key_id": "mutagenic_serum",
            "name": "Mutagenic Serum",
            "type": "Active",
            "mp_cost": 5,
            "buff_data": {"STR_percent": 0.3, "duration": 3},
            "self_damage_percent": 0.1,
            "scaling_stat": "MAG",
        }

        engine = CombatEngine(
            player=self.player,
            monster=self.monster,
            player_skills=[skill],
            player_mp=50,
            player_class_id=6,
            action="skill:mutagenic_serum",
        )

        # Initial HP
        self.player.hp_current = 100
        engine.player_hp = 100

        result = engine.run_combat_turn()
        phrases = " ".join(result["phrases"])

        # Check for Recoil message
        self.assertIn("Recoil!", phrases)

    @patch("random.randint")
    def test_fulminating_compound_stun(self, mock_randint):
        """Test that Fulminating Compound stuns the monster."""
        # Force stun chance (assuming implementation uses randint(1, 100) <= chance*100)
        # Or random.random() < chance.
        # Code uses random.random() mostly.

        skill = {
            "key_id": "fulminating_compound",
            "name": "Fulminating Compound",
            "type": "Active",
            "mp_cost": 5,
            "status_effect": {"stun_chance": 1.0},  # 100% chance for test
            "scaling_stat": "MAG",
        }

        engine = CombatEngine(
            player=self.player,
            monster=self.monster,
            player_skills=[skill],
            player_mp=50,
            player_class_id=6,
            action="skill:fulminating_compound",
        )

        # Mock random to ensure stun proc if using random.random()
        with patch("random.random", return_value=0.0):
            result = engine.run_combat_turn()

        # Verify stun prevented monster turn
        # "phrases" should contain "reeling and misses its turn" if stunned
        phrases = " ".join(result["phrases"])
        self.assertIn("misses its turn", phrases)


if __name__ == "__main__":
    unittest.main()
