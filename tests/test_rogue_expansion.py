import unittest
from unittest.mock import MagicMock

from game_systems.combat.combat_engine import CombatEngine
from game_systems.data.skills_data import SKILLS
from game_systems.player.level_up import LevelUpSystem
from game_systems.player.player_stats import PlayerStats


class TestRogueExpansion(unittest.TestCase):
    def setUp(self):
        stats = PlayerStats(str_base=10, dex_base=20, agi_base=20)
        self.player = MagicMock(spec=LevelUpSystem)
        self.player.stats = stats
        self.player.hp_current = 100
        self.player.level = 1
        self.player.stats.get_total_stats_dict = lambda: {
            "STR": 10,
            "DEX": 20,
            "AGI": 20,
            "HP": 100,
            "MP": 100,
        }
        self.monster = {
            "name": "Test Monster",
            "HP": 500,
            "max_hp": 500,
            "ATK": 10,
            "DEF": 0,
            "debuffs": [],
        }

    def test_shadow_step_buff(self):
        """Verifies shadow_step applies next_hit_crit buff."""
        skill = SKILLS["shadow_step"]
        engine = CombatEngine(
            player=self.player,
            monster=self.monster,
            player_skills=[skill],
            player_mp=100,
            player_class_id=3,
            action="skill:shadow_step",
        )
        result = engine.run_combat_turn()

        # Buff should be in new_buffs
        crit_buff_found = False
        agi_buff_found = False
        for buff in result.get("new_buffs", []):
            if buff.get("stat") == "next_hit_crit":
                crit_buff_found = True
            elif buff.get("stat") == "AGI":
                agi_buff_found = True

        self.assertTrue(crit_buff_found, "next_hit_crit buff not found")
        self.assertTrue(agi_buff_found, "AGI buff not found")

    def test_venomous_strike_multiplier(self):
        """Verifies venomous_strike applies multiplier on poisoned target."""
        skill = SKILLS["venomous_strike"]

        # Test 1: Unpoisoned target
        engine_normal = CombatEngine(
            player=self.player,
            monster=dict(self.monster),
            player_skills=[skill],
            player_mp=100,
            player_class_id=3,
            action="skill:venomous_strike",
        )
        # Fix mock random variance
        import random

        random.seed(42)
        res_normal = engine_normal.run_combat_turn()
        dmg_normal = 500 - res_normal["monster_hp"]

        # Test 2: Poisoned target
        poisoned_monster = dict(self.monster)
        poisoned_monster["debuffs"] = [{"type": "poison", "damage": 5, "duration": 3}]

        engine_poison = CombatEngine(
            player=self.player,
            monster=poisoned_monster,
            player_skills=[skill],
            player_mp=100,
            player_class_id=3,
            action="skill:venomous_strike",
        )
        random.seed(42)
        res_poison = engine_poison.run_combat_turn()
        # monster hp might also go down by poison tick during debuff processing
        dmg_poison_attack = 500 - res_poison["monster_hp"] - 5  # subtract poison tick

        self.assertTrue(
            dmg_poison_attack > dmg_normal * 1.5, f"Expected > {dmg_normal * 1.5} dmg, got {dmg_poison_attack}"
        )

    def test_flash_powder_debuff(self):
        """Verifies flash_powder applies accuracy_percent debuff."""
        skill = SKILLS["flash_powder"]
        engine = CombatEngine(
            player=self.player,
            monster=self.monster,
            player_skills=[skill],
            player_mp=100,
            player_class_id=3,
            action="skill:flash_powder",
        )
        result = engine.run_combat_turn()

        # Should be a stat_mod debuff
        debuffs = self.monster.get("debuffs", [])
        self.assertTrue(len(debuffs) > 0, "No debuff applied")
        has_accuracy = any(d.get("type") == "stat_mod" and d.get("accuracy_percent") == -0.4 for d in debuffs)
        self.assertTrue(has_accuracy, "accuracy_percent debuff not found")

    def test_death_blossom_bleed(self):
        """Verifies death_blossom applies bleed status effect."""
        skill = SKILLS["death_blossom"]
        engine = CombatEngine(
            player=self.player,
            monster=self.monster,
            player_skills=[skill],
            player_mp=100,
            player_class_id=3,
            action="skill:death_blossom",
        )
        result = engine.run_combat_turn()

        debuffs = self.monster.get("debuffs", [])
        self.assertTrue(len(debuffs) > 0, "No debuff applied")
        has_bleed = any(d.get("type") == "bleed" and d.get("damage") == 10 for d in debuffs)
        self.assertTrue(has_bleed, "bleed debuff not found")


if __name__ == "__main__":
    unittest.main()
