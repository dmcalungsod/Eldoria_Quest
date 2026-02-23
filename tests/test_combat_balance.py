import unittest
from game_systems.combat.damage_formula import DamageFormula
from game_systems.player.player_stats import PlayerStats

class TestBalanceBasicAttack(unittest.TestCase):
    def setUp(self):
        # Warrior: STR 8, DEX 5, MAG 1
        self.warrior = PlayerStats(str_base=8, dex_base=5, mag_base=1, end_base=7, agi_base=3, lck_base=1)

        # Rogue: STR 4, DEX 7, MAG 1
        self.rogue = PlayerStats(str_base=4, dex_base=7, mag_base=1, end_base=4, agi_base=8, lck_base=3)

        # Mage: STR 2, DEX 4, MAG 9
        self.mage = PlayerStats(str_base=2, dex_base=4, mag_base=9, end_base=3, agi_base=5, lck_base=2)

        self.monster = {"DEF": 0} # Zero defense to check raw output

    def test_basic_attack_imbalance(self):
        # We use a mock random to get stable results (variance 1.0, no crit)
        import unittest.mock
        import random

        with unittest.mock.patch('random.uniform', return_value=1.0), \
             unittest.mock.patch('random.random', return_value=0.5):

            w_dmg, _, _ = DamageFormula.player_attack(self.warrior, self.monster)
            r_dmg, _, _ = DamageFormula.player_attack(self.rogue, self.monster)
            m_dmg, _, _ = DamageFormula.player_attack(self.mage, self.monster)

            print(f"\nWarrior Basic Attack: {w_dmg}")
            print(f"Rogue Basic Attack: {r_dmg}")
            print(f"Mage Basic Attack: {m_dmg}")

            # --- NEW BALANCE ASSERTIONS ---
            # Warrior: 19
            # Rogue: 16.5
            # Mage: 16

            # 1. Warrior should still be top (physically strong)
            self.assertGreaterEqual(w_dmg, r_dmg, "Warrior should deal slightly more or equal damage to Rogue")
            self.assertGreater(w_dmg, m_dmg, "Warrior should outdamage Mage")

            # 2. But the gap should be small (< 5 points)
            gap = w_dmg - m_dmg
            self.assertLess(gap, 5, f"Damage gap ({gap}) is too high! Should be < 5.")

            # 3. Rogue and Mage should be comparable (< 2 point diff)
            diff = abs(r_dmg - m_dmg)
            self.assertLess(diff, 2, f"Rogue and Mage gap ({diff}) is too high! Should be < 2.")

            # 4. Check absolute values to ensure formula is working as expected
            self.assertAlmostEqual(w_dmg, 19, delta=1, msg="Warrior damage unexpected")
            self.assertAlmostEqual(r_dmg, 16, delta=1, msg="Rogue damage unexpected")
            self.assertAlmostEqual(m_dmg, 16, delta=1, msg="Mage damage unexpected")

if __name__ == "__main__":
    unittest.main()
