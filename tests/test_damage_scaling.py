import unittest

from game_systems.combat.damage_formula import DamageFormula
from game_systems.player.player_stats import PlayerStats


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
        # Mock skill using STR scaling
        skill_str = {
            "key_id": "test_strike",
            "scaling_stat": "STR",
            "scaling_factor": 2.0,
            "power_multiplier": 1.0,
        }

        # Damage should be based on STR (10) * 2.0 * 1.0 = 20 (roughly, before variance)
        dmg, _, _ = DamageFormula.player_skill(self.stats, self.monster, skill_str, 1)
        # With variance 0.9-1.1, expected around 18-22
        self.assertTrue(15 <= dmg <= 25, f"Expected damage around 20, got {dmg}")

        # Mock skill using MAG scaling
        skill_mag = {
            "key_id": "test_spell",
            "scaling_stat": "MAG",
            "scaling_factor": 2.0,
            "power_multiplier": 1.0,
        }

        # Damage should be based on MAG (20) * 2.0 * 1.0 = 40 (roughly)
        dmg, _, _ = DamageFormula.player_skill(self.stats, self.monster, skill_mag, 1)
        self.assertTrue(30 <= dmg <= 50, f"Expected damage around 40, got {dmg}")

    def test_dynamic_scaling_factor(self):
        # Mock skill with high factor
        skill_heavy = {
            "key_id": "heavy_hit",
            "scaling_stat": "STR",
            "scaling_factor": 5.0, # 10 * 5 = 50
            "power_multiplier": 1.0,
        }

        dmg, _, _ = DamageFormula.player_skill(self.stats, self.monster, skill_heavy, 1)
        self.assertTrue(40 <= dmg <= 60, f"Expected damage around 50, got {dmg}")

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

if __name__ == '__main__':
    unittest.main()
