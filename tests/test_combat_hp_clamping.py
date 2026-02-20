import unittest
from unittest.mock import MagicMock

from game_systems.combat.combat_engine import CombatEngine


class TestHPClamping(unittest.TestCase):
    def setUp(self):
        # Mock Player (LevelUpSystem wrapper)
        self.mock_player = MagicMock()
        self.mock_player.hp_current = 100
        self.mock_player.stats.max_hp = 100
        self.mock_player.level = 1

        # Mock Monster
        self.mock_monster = {
            "name": "Goblin",
            "HP": 100,
            "max_hp": 100,
            "MP": 10,
            "ATK": 10,
            "DEF": 0,
            "drops": [],
            "skills": []
        }

        self.stats_dict = {"HP": 100, "MP": 50, "STR": 10, "DEF": 0, "AGI": 10}

        # Instantiate CombatEngine
        self.engine = CombatEngine(
            player=self.mock_player,
            monster=self.mock_monster,
            player_skills=[],
            player_mp=50,
            player_class_id=1,
            stats_dict=self.stats_dict,
            action="attack"
        )

    def test_monster_hp_clamping(self):
        # Force huge damage to monster
        self.engine.player_stance = "aggressive" # 1.2x damage

        # Mock DamageFormula to return huge damage
        with unittest.mock.patch('game_systems.combat.damage_formula.DamageFormula.player_attack') as mock_dmg:
            mock_dmg.return_value = (200, False, "hit") # 200 damage

            # Run turn
            self.engine.run_combat_turn()

            # Verify monster HP is 0, not negative
            self.assertEqual(self.engine.monster_hp, 0)

    def test_player_hp_clamping(self):
        # Force huge damage to player
        self.engine.action = "defend" # Defensive stance reduces damage, but we want to test massive hit
        self.engine.action = "attack" # Back to attack so we get hit

        # Mock Monster AI to attack
        with unittest.mock.patch('game_systems.monsters.monster_actions.MonsterAI.choose_action') as mock_ai:
            mock_ai.return_value = {"type": "attack"}

            # Mock DamageFormula to return huge damage
            with unittest.mock.patch('game_systems.combat.damage_formula.DamageFormula.monster_attack') as mock_dmg:
                mock_dmg.return_value = (200, False, "hit") # 200 damage

                # Run turn
                self.engine.run_combat_turn()

                # Verify player HP is 0, not negative
                self.assertEqual(self.engine.player_hp, 0)

if __name__ == '__main__':
    unittest.main()
