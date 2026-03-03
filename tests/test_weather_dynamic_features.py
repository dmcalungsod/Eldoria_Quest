import sys
from unittest.mock import MagicMock

# Mock pymongo
mock_pymongo = MagicMock()
mock_pymongo.errors = MagicMock()
sys.modules["pymongo"] = mock_pymongo
sys.modules["pymongo.errors"] = mock_pymongo.errors

import unittest
from unittest.mock import patch

from game_systems.adventure.adventure_session import AdventureSession
from game_systems.combat.combat_engine import CombatEngine
from game_systems.core.world_time import Weather


class TestDynamicWeather(unittest.TestCase):
    def setUp(self):
        # Mock Player wrapper for CombatEngine
        self.mock_player = MagicMock()
        self.mock_player.level = 10
        self.mock_player.stats = MagicMock()
        self.mock_player.stats.max_hp = 100
        self.mock_player.stats.max_mp = 50
        self.mock_player.stats.get_total_stats_dict.return_value = {"HP": 100, "MP": 50, "STR": 10, "DEX": 10}
        self.mock_player.hp_current = 100
        self.mock_player.stats.get_base_stats_dict.return_value = {"STR": 10, "DEX": 10, "HP": 100}

        # Basic Monster
        self.monster = {"name": "Test Goblin", "HP": 100, "max_hp": 100, "ATK": 10, "DEF": 0, "MP": 0, "debuffs": []}

        # Skills
        self.skills = []

    def test_combat_weather_modifiers_blizzard(self):
        """Test Blizzard modifiers: ICE boosted, FIRE nerfed"""
        engine = CombatEngine(
            self.mock_player,
            self.monster,
            self.skills,
            50,
            1,
            weather=Weather.BLIZZARD,
            # Need to provide stats_dict to avoid attribute error if engine tries to access it
            stats_dict={"HP": 100, "MP": 50},
            base_stats_dict={"HP": 100, "MP": 50},
        )

        # Test ICE (should be +20%)
        # Note: In actual code it's int(dmg * 1.2)
        dmg_ice = engine._apply_weather_modifiers(100, "ice")
        self.assertEqual(dmg_ice, 120)

        # Test FIRE (should be -20%)
        # Note: In actual code it's int(dmg * 0.8)
        dmg_fire = engine._apply_weather_modifiers(100, "fire")
        self.assertEqual(dmg_fire, 80)

        # Test PHYSICAL (no change)
        dmg_phys = engine._apply_weather_modifiers(100, "physical")
        self.assertEqual(dmg_phys, 100)

    def test_combat_weather_modifiers_sandstorm(self):
        """Test Sandstorm modifiers: WIND boosted, EARTH boosted"""
        engine = CombatEngine(
            self.mock_player,
            self.monster,
            self.skills,
            50,
            1,
            weather=Weather.SANDSTORM,
            stats_dict={"HP": 100, "MP": 50},
            base_stats_dict={"HP": 100, "MP": 50},
        )

        dmg_wind = engine._apply_weather_modifiers(100, "wind")
        self.assertEqual(dmg_wind, 120)  # +20%

        dmg_earth = engine._apply_weather_modifiers(100, "earth")
        self.assertEqual(dmg_earth, 110)  # +10%

    def test_adventure_session_environmental_hazard(self):
        """Test non-combat environmental hazard in AdventureSession"""
        mock_db = MagicMock()

        session = AdventureSession(mock_db, MagicMock(), MagicMock(), 12345)
        session.logs = []

        # Setup context
        context = {
            "player_stats": MagicMock(max_hp=100, max_mp=50),
            "stats_dict": {"HP": 100, "MP": 50},
            "vitals": {"current_hp": 100, "current_mp": 50},
            "active_boosts": {},
            "event_type": None,
        }

        # Inject BLIZZARD and force random hit
        # We call _apply_environmental_effects directly
        with patch("random.random", return_value=0.1):  # < 0.30
            session._apply_environmental_effects(context, Weather.BLIZZARD, persist=False)

            # Check logs for "Freezing Winds"
            # The actual message is: "❄️ **Freezing Winds:** The blizzard bites deep, dealing **4** cold damage!"
            found = any("Freezing Winds" in msg for msg in session.logs)
            self.assertTrue(found, f"Logs: {session.logs}")

            # Check HP reduction
            # 4% of 100 = 4 damage
            self.assertEqual(context["vitals"]["current_hp"], 96)

    def test_combat_weather_start_of_turn_sandstorm(self):
        """Test Sandstorm start of turn damage"""
        engine = CombatEngine(
            self.mock_player,
            self.monster,
            self.skills,
            50,
            1,
            weather=Weather.SANDSTORM,
            stats_dict={"HP": 100, "MP": 50},
            base_stats_dict={"HP": 100, "MP": 50},
        )

        # Mock random to trigger effect
        with patch("random.random", return_value=0.1):  # < 0.20
            log = []
            engine._handle_weather_events(log)
            self.assertTrue(any("SANDSTORM" in msg for msg in log), f"Log: {log}")
            # Damage is 3% of 100 = 3
            self.assertEqual(engine.player_hp, 97)


if __name__ == "__main__":
    unittest.main()
