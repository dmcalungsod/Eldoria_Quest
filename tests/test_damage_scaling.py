import os
import sys
import unittest

# Add repo root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game_systems.combat.damage_formula import DamageFormula  # noqa: E402
from game_systems.player.player_stats import PlayerStats  # noqa: E402


class TestDamageScaling(unittest.TestCase):
    def setUp(self):
        # Setup mock stats: STR=10, MAG=20, END=10, HP=100
        self.stats = PlayerStats()
        self.stats._stats["STR"].base = 10
        self.stats._stats["MAG"].base = 20
        self.stats._stats["END"].base = 10
        self.stats._stats["LCK"].base = 0

        self.monster = {"DEF": 0, "HP": 1000}

    def test_dynamic_scaling_stat(self):
        # Mock random to avoid variance and crits
        import unittest.mock

        with (
            unittest.mock.patch("random.uniform", return_value=1.0),
            unittest.mock.patch("random.random", return_value=0.5),
        ):
            # Mock skill using STR scaling
            skill_str = {
                "key_id": "test_strike",
                "scaling_stat": "STR",
                "scaling_factor": 2.0,
                "power_multiplier": 1.0,
            }

            # Damage should be based on STR (10) * 2.0 * 1.0 = 20
            # PLUS Secondary Stat Bonus (0.5x scaling from other stats)
            # MAG (20) * 0.5 * 1.0 = 10
            # DEX (1) * 0.5 * 1.0 = 0.5
            # Total ~ 30.5
            dmg, _, _ = DamageFormula.player_skill(self.stats, self.monster, skill_str, 1)
            self.assertTrue(28 <= dmg <= 33, f"Expected damage around 30.5, got {dmg}")

            # Mock skill using MAG scaling
            skill_mag = {
                "key_id": "test_spell",
                "scaling_stat": "MAG",
                "scaling_factor": 2.0,
                "power_multiplier": 1.0,
            }

            # Damage should be based on MAG (20) * 2.0 * 1.0 = 40
            # PLUS Secondary Stat Bonus (STR=10->5, DEX=1->0.5) = 5.5
            # Total ~ 45.5
            dmg, _, _ = DamageFormula.player_skill(self.stats, self.monster, skill_mag, 1)
            self.assertTrue(43 <= dmg <= 48, f"Expected damage around 45.5, got {dmg}")

    def test_dynamic_scaling_factor(self):
        # Mock random to ensure consistent damage (no crits, variance 1.0)
        import unittest.mock

        with (
            unittest.mock.patch("random.uniform", return_value=1.0),
            unittest.mock.patch("random.random", return_value=0.5),
        ):
            # Mock skill with high factor
            skill_heavy = {
                "key_id": "heavy_hit",
                "scaling_stat": "STR",
                "scaling_factor": 5.0,  # 10 * 5 = 50
                "power_multiplier": 1.0,
            }

            # Base: 50. Secondary (MAG=10, DEX=0.5) = 10.5. Total 60.5.
            dmg, _, _ = DamageFormula.player_skill(self.stats, self.monster, skill_heavy, 1)
            self.assertTrue(58 <= dmg <= 63, f"Expected damage around 60.5, got {dmg}")

    def test_player_heal_max_hp_logic(self):
        # Test healing cap and max_hp consistency
        skill_heal = {
            "key_id": "heal",
            "heal_power": 50,
            "scaling_stat": "MAG",
            "scaling_factor": 1.0,
        }

        # Max HP is approx 50 + (10 * 10 * 1.0) = 150 (since END is 10)
        # MAG bonus is 20 * 1.0 = 20
        # Base heal 50 + 20 = 70.

        # Current HP 1. Healed to ~71.
        healed, new_hp, _ = DamageFormula.player_heal(self.stats, 1, skill_heal, 1)

        self.assertTrue(new_hp > 1)
        self.assertTrue(healed > 0)

        # Verify it respects max hp
        # Set current HP to max-1
        max_hp = self.stats.max_hp
        healed, new_hp, _ = DamageFormula.player_heal(self.stats, max_hp - 1, skill_heal, 1)
        self.assertEqual(new_hp, max_hp)
        self.assertEqual(healed, 1)


if __name__ == "__main__":
    unittest.main()
