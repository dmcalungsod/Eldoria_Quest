import sys
from unittest.mock import MagicMock

# Mock pymongo globally BEFORE any other imports
sys.modules["pymongo"] = MagicMock()

import unittest
from unittest.mock import patch
from game_systems.adventure.adventure_session import AdventureSession, WEATHER_DMG_PCT, WEATHER_FLEE_PENALTY
from game_systems.world_time import Weather
from game_systems.player.player_stats import PlayerStats

class TestWeatherEffects(unittest.TestCase):
    def setUp(self):
        self.mock_db = MagicMock()
        self.mock_quest = MagicMock()
        self.mock_inv = MagicMock()
        self.discord_id = 12345

        # Setup basic session context
        # 10 END -> 150 HP (50 base + 10*10)
        self.player_stats = PlayerStats(agi_base=10, end_base=10)
        self.max_hp = self.player_stats.max_hp

        self.context_bundle = {
            "stats": self.player_stats.to_dict(),
            "buffs": [],
            "player": {
                "current_hp": self.max_hp,
                "current_mp": 50,
                "level": 1,
                "class_id": "warrior",
                "experience": 0,
                "exp_to_next": 100
            },
            "skills": [],
            "active_session": {
                "location_id": "molten_caldera",
                "active": 1,
                "logs": "[]",
                "loot_collected": "{}",
                "active_monster_json": None,
                "version": 1
            }
        }

        self.mock_db.get_combat_context_bundle.return_value = self.context_bundle
        self.mock_db.get_active_boosts.return_value = []

        # Initialize session
        self.session = AdventureSession(self.mock_db, self.mock_quest, self.mock_inv, self.discord_id, self.context_bundle["active_session"])

    @patch("game_systems.adventure.adventure_session.WorldTime")
    def test_ash_storm_damage(self, MockWorldTime):
        """Verify Ash Storm deals damage and logs it."""
        MockWorldTime.get_current_weather.return_value = Weather.ASH

        # Initial HP
        initial_hp = self.context_bundle["player"]["current_hp"]

        # Run step
        result = self.session.simulate_step(context_bundle=self.context_bundle)

        # Calculate expected damage
        expected_damage = int(initial_hp * WEATHER_DMG_PCT[Weather.ASH])
        expected_hp = initial_hp - expected_damage

        # Verify vitals updated in result
        self.assertEqual(result["vitals"]["current_hp"], expected_hp)

        # Verify DB update called
        self.mock_db.set_player_vitals.assert_called_with(self.discord_id, expected_hp, 50)

        # Verify Logs
        logs = result["sequence"][0]
        self.assertTrue(any("Ash Storm" in log for log in logs))
        self.assertTrue(any(f"-{expected_damage} HP" in log for log in logs))

    @patch("game_systems.adventure.adventure_session.WorldTime")
    def test_weather_death(self, MockWorldTime):
        """Verify weather can kill the player."""
        MockWorldTime.get_current_weather.return_value = Weather.ASH

        # Set HP to 1
        self.context_bundle["player"]["current_hp"] = 1

        # Run step
        result = self.session.simulate_step(context_bundle=self.context_bundle)

        # Verify Dead
        self.assertTrue(result["dead"])
        self.assertEqual(result["vitals"]["current_hp"], 0)

        # Verify Logs
        logs = result["sequence"][0]
        self.assertTrue(any("succumbed to the elements" in log for log in logs))

    @patch("game_systems.adventure.adventure_session.WorldTime")
    @patch("game_systems.adventure.adventure_session.random.randint")
    def test_fog_flee_penalty(self, mock_randint, MockWorldTime):
        """Verify Fog reduces flee chance."""
        MockWorldTime.get_current_weather.return_value = Weather.FOG

        # Setup Active Monster
        self.session.active_monster = {"level": 1, "name": "Goblin"}

        # Calculate Chance:
        # AGI 10, Monster Lvl 1 -> Bonus (10-1)*2 = 18
        # Base 50 + 18 = 68%
        # Fog Penalty = 20%
        # Final Chance = 48%

        # Case 1: Roll 50 (Fail due to penalty, would succeed without)
        mock_randint.return_value = 50

        result = self.session.simulate_step(context_bundle=self.context_bundle, action="flee")

        # Verify Failure
        logs = result["sequence"][0]
        self.assertTrue(any("Escape Failed" in log for log in logs))
        self.assertTrue(any("fog obscures" in log for log in logs))

        # Verify Chance in log matches expected
        self.assertTrue(any("Chance: 48%" in log for log in logs))

    @patch("game_systems.adventure.adventure_session.WorldTime")
    @patch("game_systems.adventure.adventure_session.random.randint")
    def test_no_flee_penalty_clear(self, mock_randint, MockWorldTime):
        """Verify Clear weather has no penalty."""
        MockWorldTime.get_current_weather.return_value = Weather.CLEAR

        # Setup Active Monster
        self.session.active_monster = {"level": 1, "name": "Goblin"}

        # Chance: 68% (calculated above)

        # Case 1: Roll 50 (Success)
        mock_randint.return_value = 50

        result = self.session.simulate_step(context_bundle=self.context_bundle, action="flee")

        # Verify Success
        logs = result["sequence"][0]
        self.assertTrue(any("You fled!" in log for log in logs))
        self.assertTrue(any("Chance: 68%" in log for log in logs))
