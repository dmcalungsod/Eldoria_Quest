import os
import sys
import unittest
from unittest.mock import patch

# Add repo root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game_systems.combat.damage_formula import DamageFormula
from game_systems.player.player_stats import PlayerStats


class TestCombatDefenseCurve(unittest.TestCase):
    def setUp(self):
        # Setup basic player stats
        self.stats = PlayerStats(str_base=10, end_base=10, mag_base=10, dex_base=10, agi_base=10, lck_base=10)
        # STR=10 -> Bonus = 10 * 2.0 = 20
        # DEX=10 -> Bonus = 10 * 1.0 = 10
        # MAG=10 -> Bonus = 10 * 0.5 = 5
        # Attack Power = 35

    def test_player_attack_defense_reduction(self):
        """
        Verify that monster Defense reduces player damage according to the formula:
        reduction = DEF * (0.3 + 0.2 * min(1, DEF/100))
        """
        base_ap = 30  # Calculated from setup (10*2.0 + 10*0.5 + 10*0.5)

        # Test Cases: (Monster DEF, Expected Reduction, Expected Damage)
        # 1. DEF = 0 -> Red = 0 * 0.3 = 0. Dmg = 30.
        # 2. DEF = 50 -> Red = 50 * (0.3 + 0.1) = 20. Dmg = 10.
        # 3. DEF = 100 -> Red = 100 * (0.3 + 0.2) = 50. Dmg = 1 (Floor).
        # 4. DEF = 200 -> Red = 200 * 0.5 = 100. Dmg = 1 (Floor).

        test_cases = [(0, 30), (50, 10), (100, 1), (200, 1)]  # 30 - 20 = 10

        with patch("random.uniform", return_value=1.0), patch("random.random", return_value=0.5):  # No crit
            for def_val, expected_dmg in test_cases:
                monster = {"DEF": def_val}
                dmg, is_crit, _ = DamageFormula.player_attack(self.stats, monster)

                self.assertEqual(
                    dmg,
                    expected_dmg,
                    f"Failed for DEF={def_val}. Expected {expected_dmg}, got {dmg}",
                )
                self.assertFalse(is_crit)

    def test_monster_attack_player_defense_scaling(self):
        """
        Verify that player END scales defense and reduces monster damage.
        Player Defense = END * 1.5 (Tier 1)
        """
        # Monster ATK = 100
        monster = {"ATK": 100}

        # Test Cases: (Player END, Expected Defense, Expected Reduction, Expected Damage)
        # 1. END = 10 -> Def = 15. Red = 15 * (0.3 + 0.2*0.15) = 15 * 0.33 = 4.95 -> 4.95.
        #    Dmg = 100 - 4.95 = 95.05 -> 95.
        #    Chip Floor = 100 * 0.05 = 5. 95 > 5.

        # 2. END = 100 -> Def = 150. Red = 150 * 0.5 = 75.
        #    Dmg = 100 - 75 = 25.

        # 3. END = 200 -> Def = 337 (Tiered Bonus logic: 100*1.5 + 100*1.5*1.25 = 150 + 187.5 = 337.5 -> 337).
        #    Red = 337 * 0.5 = 168.5.
        #    Base Dmg = 100 - 168.5 < 0.
        #    Chip Floor = 5.
        #    Final Dmg = 5.

        # Let's verify END=10 math carefully.
        # Def = 15.
        # min(1, 15/100) = 0.15.
        # Mul = 0.3 + 0.2 * 0.15 = 0.3 + 0.03 = 0.33.
        # Red = 15 * 0.33 = 4.95.
        # Dmg = 100 - 4.95 = 95.05 -> int(95.05) = 95.

        test_cases = [(10, 95), (100, 25), (200, 5)]  # Chip damage floor

        with patch("random.uniform", return_value=1.0), patch("random.random", return_value=0.5):  # No dodge, no crit
            for end_val, expected_dmg in test_cases:
                # Update stats
                self.stats._stats["END"].base = end_val
                # Recalculate bonuses if needed (PlayerStats doesn't cache derived stats so it's fine)

                dmg, is_crit, _ = DamageFormula.monster_attack(monster, self.stats)

                self.assertEqual(
                    dmg,
                    expected_dmg,
                    f"Failed for END={end_val}. Expected {expected_dmg}, got {dmg}",
                )

    def test_monster_chip_damage_floor(self):
        """
        Verify the 5% chip damage floor explicitly.
        """
        monster = {"ATK": 100}

        # Set player END high enough to negate all damage
        # ATK 100. Need Red > 100.
        # If END=200, Red=168.
        self.stats._stats["END"].base = 200

        with patch("random.uniform", return_value=1.0), patch("random.random", return_value=0.5):
            dmg, _, _ = DamageFormula.monster_attack(monster, self.stats)

            expected_chip = int(100 * 0.05)  # 5
            self.assertEqual(dmg, expected_chip, f"Chip damage should be {expected_chip}, got {dmg}")

    def test_crit_multiplier(self):
        """
        Verify crit multiplier is 1.75x for players.
        """
        base_ap = 30  # Setup default (10/10/10 -> 20 + 5 + 5 = 30)
        monster = {"DEF": 0}

        # Force Crit
        # Damage = 30 * 1.75 = 52.5 -> 52

        with (
            patch("random.uniform", return_value=1.0),
            patch("random.random", return_value=0.0),
        ):  # Force Crit (0.0 < chance)
            dmg, is_crit, event = DamageFormula.player_attack(self.stats, monster)

            self.assertTrue(is_crit)
            self.assertEqual(event, "crit")
            self.assertEqual(dmg, 52)


if __name__ == "__main__":
    unittest.main()
