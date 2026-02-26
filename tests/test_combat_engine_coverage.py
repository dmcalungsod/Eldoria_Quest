import unittest
from unittest.mock import MagicMock, patch

from game_systems.combat.combat_engine import CombatEngine
from game_systems.core.world_time import Weather


class TestCombatEngineCoverage(unittest.TestCase):
    def setUp(self):
        self.player = MagicMock()
        self.player.stats.get_total_stats_dict.return_value = {
            "HP": 100, "MP": 50, "STR": 10, "LCK": 5, "AGI": 10, "DEX": 10, "INT": 10, "END": 10, "MAG": 10
        }
        self.player.stats.max_hp = 100
        self.player.stats.max_mp = 50
        self.player.hp_current = 100
        self.player.level = 1

        self.monster = {"name": "Goblin", "HP": 50, "max_hp": 50, "ATK": 10, "level": 1, "tier": "Normal"}
        self.skills = []

    def _create_engine(self, weather=Weather.CLEAR, action="attack", class_id=1):
        return CombatEngine(
            self.player,
            self.monster,
            self.skills,
            player_mp=50,
            player_class_id=class_id,
            weather=weather,
            action=action
        )

    @patch('game_systems.combat.combat_engine.random.random')
    @patch('game_systems.combat.combat_engine.random.choice')
    def test_handle_weather_events_storm_monster_hit(self, mock_choice, mock_random):
        """Test Storm lightning hitting monster."""
        engine = self._create_engine(weather=Weather.STORM)
        mock_random.return_value = 0.1 # Trigger lightning (< 0.15)
        mock_choice.return_value = False # Target Monster (False)

        log = []
        engine._handle_weather_events(log)

        self.assertLess(engine.monster_hp, 50)
        self.assertIn("lightning bolt strikes the **Goblin**", log[0])

    @patch('game_systems.combat.combat_engine.random.random')
    def test_handle_weather_events_ash(self, mock_random):
        """Test Ash Storm damage."""
        engine = self._create_engine(weather=Weather.ASH)
        log = []
        engine._handle_weather_events(log)
        self.assertLess(engine.player_hp, 100)
        self.assertIn("choking ash burns", log[0])

    @patch('game_systems.combat.combat_engine.random.random')
    def test_handle_weather_events_miasma(self, mock_random):
        """Test Miasma damage."""
        engine = self._create_engine(weather=Weather.MIASMA)
        mock_random.return_value = 0.1 # Trigger (< 0.25)
        log = []
        engine._handle_weather_events(log)
        self.assertLess(engine.player_hp, 100)
        self.assertIn("toxic fumes", log[0].lower())

    def test_detect_element_fallback(self):
        """Test element detection by name/emoji."""
        engine = self._create_engine()

        self.assertEqual(engine._detect_element({"name": "Fireball"}), "fire")
        self.assertEqual(engine._detect_element({"emoji": "❄️"}), "ice")
        self.assertEqual(engine._detect_element({"name": "Slash"}), "physical")

    def test_apply_weather_modifiers(self):
        """Test weather damage modifiers."""
        engine = self._create_engine(weather=Weather.RAIN)
        self.assertEqual(engine._apply_weather_modifiers(100, "fire"), 80)
        self.assertEqual(engine._apply_weather_modifiers(100, "lightning"), 120)

        engine.weather = Weather.SNOW
        self.assertEqual(engine._apply_weather_modifiers(100, "ice"), 120)
        self.assertEqual(engine._apply_weather_modifiers(100, "fire"), 90)

    def test_resolve_special_ability_cleric_heal(self):
        """Test Cleric Smite heal logic."""
        # Class 4 = Cleric (Smite)
        engine = self._create_engine(action="special_ability", class_id=4)
        engine.player_hp = 50 # Injured

        log = []
        turn_report = {}

        # Smite has heal=20 + level*2 = 22
        # Mock DamageFormula to return predictable damage so we don't crash
        with patch('game_systems.combat.combat_engine.DamageFormula.player_attack', return_value=(10, False, "hit")):
            engine._resolve_special_ability(log, turn_report)

        self.assertEqual(engine.player_hp, 72) # 50 + 22
        self.assertIn("Smite", log[0])

    def test_execute_player_skill_recoil(self):
        """Test skill recoil."""
        engine = self._create_engine()
        skill = {
            "name": "Life Tap",
            "mp_cost": 0,
            "self_damage_percent": 0.1,
            # No heal, no buff -> Offensive
        }

        log = []
        turn_report = {}

        with patch('game_systems.combat.combat_engine.DamageFormula.player_skill', return_value=(20, False, "hit")):
            engine._execute_player_skill(skill, log, turn_report)

        # Dmg dealt 20. Recoil 10% = 2.
        self.assertEqual(engine.player_hp, 98)
        self.assertIn("Recoil", log[-1])

    def test_apply_monster_debuff_refresh(self):
        """Test refreshing monster debuffs."""
        engine = self._create_engine()
        skill = {
            "name": "Poison Dart",
            "debuff": {"poison": 5, "duration": 3},
            "scaling_stat": "DEX"
        }

        # Apply once
        engine._apply_monster_debuff(skill)
        self.assertEqual(len(engine.monster["debuffs"]), 1)
        self.assertEqual(engine.monster["debuffs"][0]["duration"], 3)

        # Apply again (Refresh)
        skill["debuff"]["duration"] = 5
        msg = engine._apply_monster_debuff(skill)

        self.assertEqual(len(engine.monster["debuffs"]), 1)
        self.assertEqual(engine.monster["debuffs"][0]["duration"], 5)
        self.assertIn("is refreshed", msg)

    def test_process_monster_debuffs_stat_mod(self):
        """Test stat mod debuff application."""
        engine = self._create_engine()
        skill = {
            "name": "Weaken",
            "debuff": {"ATK_percent": -0.5, "duration": 2, "type": "stat_mod"}
        }

        engine._apply_monster_debuff(skill)

        # Verify monster effective stats
        eff_monster = engine._get_effective_monster_stats()
        # Base ATK 10. Mod -50% -> 5.
        self.assertEqual(eff_monster["ATK"], 5)

    def test_player_victory_bloodlust(self):
        """Test Bloodlust passive."""
        engine = self._create_engine()
        engine.player_hp = 50
        engine.player_skills = [
            {"type": "Passive", "passive_bonus": {"kill_heal_percent": 0.1}}
        ]

        log = []
        turn_report = {}

        with patch('game_systems.combat.combat_engine.ExpCalculator.calculate_exp', return_value=100), \
             patch('game_systems.combat.combat_engine.AurumCalculator.calculate_drop', return_value=50):
            engine._player_victory(log, turn_report)

        # Max HP 100. 10% = 10.
        self.assertEqual(engine.player_hp, 60)
        self.assertIn("Bloodlust", log[-2]) # Before victory msg

    def test_run_combat_turn_exception(self):
        """Test exception handling in run_combat_turn."""
        engine = self._create_engine()
        # Mock internal method inside the try block to raise exception
        with patch.object(engine, '_check_interrupt_mechanic', side_effect=Exception("Boom")):
            result = engine.run_combat_turn()

        self.assertIsNone(result["winner"])
        self.assertIn("interrupted by a strange force", result["phrases"][0])
