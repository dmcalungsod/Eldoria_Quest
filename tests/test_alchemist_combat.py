import sys
import os
import unittest
from unittest.mock import MagicMock

# Add repo root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game_systems.combat.combat_engine import CombatEngine
from game_systems.player.player_stats import PlayerStats

class TestAlchemistCombat(unittest.TestCase):
    def setUp(self):
        # Mock Player
        self.mock_player = MagicMock()
        self.mock_player.stats = MagicMock()
        self.mock_player.stats.get_total_stats_dict.return_value = {
            "STR": 10, "DEX": 10, "MAG": 10, "END": 10, "LCK": 10, "AGI": 10,
            "HP": 100, "MP": 100
        }
        self.mock_player.stats.max_hp = 100
        self.mock_player.stats.max_mp = 100

        self.mock_player.level = 10
        self.mock_player.hp_current = 100

        # Mock Monster
        self.monster = {
            "name": "Test Monster",
            "HP": 100,
            "max_hp": 100,
            "ATK": 10,
            "DEF": 10,
            "MP": 10,
            "skills": []
        }

        # Base Stats Dict
        self.stats_dict = self.mock_player.stats.get_total_stats_dict()

    def test_vitriol_bomb_debuff(self):
        """Test that Vitriol Bomb applies END_percent debuff."""
        # Skill Data
        skill = {
            "key_id": "vitriol_bomb",
            "name": "Vitriol Bomb",
            "type": "Active",
            "mp_cost": 5,
            "debuff": {"END_percent": -0.5, "duration": 3}, # -50% END
            "scaling_stat": "DEX"
        }

        # Initialize Engine
        engine = CombatEngine(
            player=self.mock_player,
            monster=self.monster,
            player_skills=[skill],
            player_mp=50,
            player_class_id=6,
            stats_dict=self.stats_dict,
            action="skill:vitriol_bomb"
        )

        # Run Turn
        result = engine.run_combat_turn()

        # Check Log for specific phrase?
        # Better: Check monster debuffs directly
        # But engine.monster is modified in place?
        # CombatEngine copies monster? No, uses passed reference.

        self.assertIn("debuffs", self.monster)
        debuffs = self.monster["debuffs"]
        self.assertTrue(any(d["name"] == "Vitriol Bomb" for d in debuffs))

        applied_debuff = next(d for d in debuffs if d["name"] == "Vitriol Bomb")
        self.assertEqual(applied_debuff["END_percent"], -0.5)

        # Verify stats recalculation
        # effective_monster = engine._get_effective_monster_stats()
        # This method is internal, but we can check if it works by manually invoking it
        # or checking if subsequent damage calculation would use it.
        # Let's just check _get_effective_monster_stats logic if possible,
        # but since I can't easily access the engine instance after run_combat_turn returns...
        # I'll rely on the debuff being present.

    def test_fulminating_compound_stun(self):
        """Test that Fulminating Compound can stun."""
        # Skill Data
        skill = {
            "key_id": "fulminating_compound",
            "name": "Fulminating Compound",
            "type": "Active",
            "mp_cost": 5,
            "status_effect": {"stun_chance": 1.0}, # 100% chance for test
            "scaling_stat": "MAG"
        }

        engine = CombatEngine(
            player=self.mock_player,
            monster=self.monster,
            player_skills=[skill],
            player_mp=50,
            player_class_id=6,
            stats_dict=self.stats_dict,
            action="skill:fulminating_compound"
        )

        # Mock Random to ensure stun hits if there's a roll (though 1.0 should pass)

        result = engine.run_combat_turn()

        # If stun works, the monster should NOT attack.
        # "hits_taken" in turn_report should be 0.
        turn_report = result["turn_report"]
        self.assertEqual(turn_report["hits_taken"], 0, "Monster attacked despite 100% stun chance!")

        # Also check for "stunned" phrase in log
        log_str = " ".join(result["phrases"])
        self.assertTrue("stunned" in log_str.lower() or "misses its turn" in log_str, "No stun message found in log.")

    def test_mutagenic_serum_recoil(self):
        """Test that Mutagenic Serum causes recoil damage."""
        skill = {
            "key_id": "mutagenic_serum",
            "name": "Mutagenic Serum",
            "type": "Active",
            "mp_cost": 5,
            "buff_data": {"STR_percent": 0.3, "duration": 3},
            "self_damage_percent": 0.1, # 10% Recoil
        }

        # Set specific HP
        self.mock_player.hp_current = 100
        engine = CombatEngine(
            player=self.mock_player,
            monster=self.monster,
            player_skills=[skill],
            player_mp=50,
            player_class_id=6,
            stats_dict=self.stats_dict,
            action="skill:mutagenic_serum"
        )

        # Prevent monster from dealing damage so we only test recoil
        engine.monster["ATK"] = 0

        result = engine.run_combat_turn()

        # Check for recoil message specifically to be sure
        log_str = " ".join(result["phrases"])
        self.assertTrue("recoil" in log_str.lower(), "Recoil message not found in log.")

        # Recoil logic expectation:
        # If using Max HP (100) * 0.1 = 10 dmg.
        self.assertLess(result["hp_current"], 91, "HP should be reduced by at least 10 (Recoil).")

    def test_zero_damage_recoil(self):
        """Test that offensive skills dealing 0 damage do NOT trigger Max HP recoil."""
        # Skill that has recoil but deals damage
        skill = {
            "key_id": "reckless_swing",
            "name": "Reckless Swing",
            "type": "Active",
            "mp_cost": 5,
            "power_multiplier": 2.0,
            "self_damage_percent": 0.1, # 10% Recoil of damage dealt
            "scaling_stat": "STR"
        }

        # Force damage to 0 by giving monster huge DEF
        self.monster["DEF"] = 9999

        engine = CombatEngine(
            player=self.mock_player,
            monster=self.monster,
            player_skills=[skill],
            player_mp=50,
            player_class_id=1,
            stats_dict=self.stats_dict,
            action="skill:reckless_swing"
        )

        # Monster should not attack (prevent noise)
        engine.monster["ATK"] = 0

        result = engine.run_combat_turn()

        # Damage dealt should be ~1 (min damage) or 0 if blocked completely?
        # DamageFormula usually returns max(1, ...) or min damage.
        # If damage is low, recoil should be low.
        # If fallback logic was buggy, it would take 10% Max HP (10 dmg).
        # We expect recoil to be based on actual damage (which is small).

        # Let's check damage dealt in turn_report
        # But turn_report only tracks total damage? No, "damage_taken" by player.
        # We want damage dealt to monster.
        # self.monster["max_hp"] - result["monster_hp"]

        dmg_dealt = 100 - result["monster_hp"]
        expected_recoil = max(1, int(dmg_dealt * 0.1))

        # Max HP recoil would be 10.
        # Damage dealt with 9999 DEF should be min_damage (e.g. 1 or 5% ATK).
        # Player stats are low (10 STR), so damage is definitely low.

        hp_loss = 100 - result["hp_current"]

        # If bug exists, hp_loss would be ~10.
        # If fix exists, hp_loss should be ~1.

        self.assertLess(hp_loss, 5, f"Recoil was too high ({hp_loss}), likely used Max HP scaling instead of Damage scaling.")

if __name__ == "__main__":
    unittest.main()
