import unittest
from unittest.mock import MagicMock

from game_systems.combat.combat_effects import CombatEffects
from game_systems.combat.combat_engine import CombatEngine


class TestCombatDebuffs(unittest.TestCase):
    def setUp(self):
        self.player = MagicMock()
        self.player.is_stunned = False
        self.player.is_silenced = False
        self.player.stats.max_hp = 100
        self.player.hp_current = 100
        self.player.level = 10
        self.player.add_exp = MagicMock(return_value=False)
        self.player.stats.get_total_stats_dict = MagicMock(
            return_value={
                "HP": 100,
                "MP": 50,
                "STR": 20,
                "DEX": 10,
                "MAG": 10,
                "END": 20,
                "LCK": 10,
                "DEF": 5,
                "ATK": 10,
            }
        )

        self.monster = {
            "name": "Test Monster",
            "HP": 100,
            "max_hp": 100,
            "ATK": 50,
            "DEF": 10,
            "level": 5,
            "debuffs": [],
        }

        self.stats_dict = {
            "HP": 100,
            "MP": 50,
            "STR": 20,
            "DEX": 10,
            "MAG": 10,
            "END": 20,
            "LCK": 10,
            "DEF": 5,
            "ATK": 10,
        }

        self.taunt_skill = {
            "key_id": "taunt",
            "name": "Taunt",
            "type": "Active",
            "mp_cost": 0,
            "debuff": {"ATK_percent": -0.5, "duration": 3},
            "scaling_stat": "END",
            "skill_level": 1,
        }

    def test_taunt_application(self):
        engine = CombatEngine(
            player=self.player,
            monster=self.monster,
            player_skills=[self.taunt_skill],
            player_mp=50,
            player_class_id=1,
            stats_dict=self.stats_dict,
            action="skill:taunt",
        )

        # Run turn to apply taunt
        result = engine.run_combat_turn()

        # Check if debuff was applied to internal state
        debuffs = engine.monster.get("debuffs", [])

        has_atk_debuff = any("ATK_percent" in d for d in debuffs)
        self.assertTrue(has_atk_debuff, "Taunt debuff not applied.")

        # Verify effective stats
        effective = engine._get_effective_monster_stats()

        expected_atk = int(50 * 0.5)  # 50% reduction
        self.assertEqual(
            effective["ATK"],
            expected_atk,
            f"ATK not reduced correctly. Expected {expected_atk}, got {effective['ATK']}",
        )

        # Test crash on process_monster_debuffs with stat mod (should pass now)
        try:
            # We need to simulate next turn or call private method
            engine.monster_hp, msgs = CombatEffects.process_monster_debuffs(engine.monster, engine.monster_hp)

            # Check duration decrement
            debuffs = engine.monster.get("debuffs", [])
            self.assertEqual(debuffs[0]["duration"], 2, "Duration not decremented.")

        except Exception as e:
            self.fail(f"_process_monster_debuffs crashed with {type(e).__name__}: {e}")


if __name__ == "__main__":
    unittest.main()
