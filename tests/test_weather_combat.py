import sys
import os
import unittest
from unittest.mock import MagicMock, patch

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock external dependencies
sys.modules["pymongo"] = MagicMock()
sys.modules["discord"] = MagicMock()

from game_systems.combat.combat_engine import CombatEngine
from game_systems.core.world_time import Weather, TimePhase

class TestWeatherCombat(unittest.TestCase):
    def setUp(self):
        self.mock_player = MagicMock()
        self.mock_player.hp_current = 100
        self.mock_player.stats = MagicMock()
        self.mock_player.stats.max_hp = 100
        self.mock_player.stats.get_total_stats_dict.return_value = {"HP": 100}

        self.monster = {"HP": 100, "max_hp": 100, "name": "Dummy"}

        # Base engine setup
        self.engine = CombatEngine(
            player=self.mock_player,
            monster=self.monster,
            player_skills=[],
            player_mp=100,
            player_class_id=1,
            stats_dict={"HP": 100}, # Explicitly provide stats_dict to avoid attribute error if mocked player fails
        )

    def test_detect_element(self):
        # Fire
        skill = {"type": "fire"}
        self.assertEqual(self.engine._detect_element(skill), "fire")
        skill = {"name": "Fireball"}
        self.assertEqual(self.engine._detect_element(skill), "fire")
        skill = {"emoji": "🔥"}
        self.assertEqual(self.engine._detect_element(skill), "fire")

        # Ice
        skill = {"name": "Frost Bolt"}
        self.assertEqual(self.engine._detect_element(skill), "ice")

        # Physical
        skill = {"name": "Slash"}
        self.assertEqual(self.engine._detect_element(skill), "physical")

    def test_rain_modifiers(self):
        self.engine.weather = Weather.RAIN

        # Fire reduced
        dmg = 100
        mod_dmg = self.engine._apply_weather_modifiers(dmg, "fire")
        self.assertEqual(mod_dmg, 80) # 0.8x

        # Lightning boosted
        dmg = 100
        mod_dmg = self.engine._apply_weather_modifiers(dmg, "lightning")
        self.assertEqual(mod_dmg, 120) # 1.2x

        # Physical unaffected
        dmg = 100
        mod_dmg = self.engine._apply_weather_modifiers(dmg, "physical")
        self.assertEqual(mod_dmg, 100)

    def test_fog_modifiers(self):
        self.engine.weather = Weather.FOG

        dmg = 100
        mod_dmg = self.engine._apply_weather_modifiers(dmg, "physical")
        self.assertEqual(mod_dmg, 90) # 0.9x

        mod_dmg = self.engine._apply_weather_modifiers(dmg, "fire")
        self.assertEqual(mod_dmg, 90) # 0.9x

    def test_storm_lightning_event(self):
        self.engine.weather = Weather.STORM
        log = []

        # Patch random to force lightning strike on player
        # random.random() calls:
        # 1. < 0.15 check (return 0.1)
        # random.choice([True, False]) calls random.choice

        with patch("random.random", side_effect=[0.1]), \
             patch("random.choice", return_value=True): # True for player

            self.engine._handle_weather_events(log)

            self.assertTrue(any("lightning bolt strikes YOU" in msg for msg in log))
            self.assertLess(self.engine.player_hp, 100)

    def test_ash_storm_event(self):
        self.engine.weather = Weather.ASH
        log = []

        self.engine._handle_weather_events(log)

        self.assertTrue(any("choking ash" in msg for msg in log))
        self.assertLess(self.engine.player_hp, 100)

if __name__ == "__main__":
    unittest.main()
