import sys
from unittest.mock import MagicMock, patch

# Mock pymongo before importing any app modules
try:
    import pymongo
    import pymongo.errors  # noqa: F401
except ImportError:
    mock_pymongo = MagicMock()
    mock_pymongo.errors = MagicMock()
    sys.modules["pymongo"] = mock_pymongo
    sys.modules["pymongo.errors"] = mock_pymongo.errors

import unittest

from game_systems.adventure.adventure_session import AdventureSession
from game_systems.world_time import TimePhase, Weather


class TestAdventureDayNight(unittest.TestCase):
    def setUp(self):
        self.mock_db = MagicMock()
        self.mock_quest = MagicMock()
        self.mock_inv = MagicMock()

        # Setup session
        self.session = AdventureSession(self.mock_db, self.mock_quest, self.mock_inv, discord_id=123456789)
        self.session.location_id = "forest_outskirts"
        self.session.logs = []

        # Default context mock
        self.mock_context = {
            "player_stats": MagicMock(max_hp=100, max_mp=50, agility=10),
            "stats_dict": {"HP": 100},
            "vitals": {"current_hp": 100, "current_mp": 50},
            "player_row": {"level": 1, "class_id": 1, "current_hp": 100, "current_mp": 50},
            "skills": [],
            "active_boosts": {},
            "event_type": None,
        }

    def test_regen_threshold_day(self):
        """Daytime should increase regen threshold (safer)."""
        with patch("game_systems.adventure.adventure_session.WorldTime") as MockTime:
            MockTime.get_current_weather.return_value = Weather.CLEAR
            MockTime.get_current_phase.return_value = TimePhase.DAY
            MockTime.get_weather_flavor.return_value = "Clear Sky"

            with patch.object(self.session, "_fetch_session_context", return_value=self.mock_context):
                # Mock random to force combat (roll > threshold)
                # Threshold = 40 (base) + 5 (CLEAR) + 5 (DAY) = 50
                # So roll > 50 triggers combat.
                with patch("random.randint", return_value=51):
                    # Mock initiate_combat to return nothing so we don't crash on monster setup
                    self.session.combat.initiate_combat = MagicMock(return_value=(None, "No monster"))

                    self.session.simulate_step(context_bundle=None)

                    # Verify logic reached combat trigger
                    self.session.combat.initiate_combat.assert_called()

    def test_regen_threshold_night(self):
        """Nighttime should decrease regen threshold (dangerous)."""
        with patch("game_systems.adventure.adventure_session.WorldTime") as MockTime:
            MockTime.get_current_weather.return_value = Weather.CLEAR
            MockTime.get_current_phase.return_value = TimePhase.NIGHT
            MockTime.get_weather_flavor.return_value = "Clear Night"

            with patch.object(self.session, "_fetch_session_context", return_value=self.mock_context):
                # Threshold = 40 (base) + 5 (CLEAR) - 10 (NIGHT) = 35
                # So roll > 35 triggers combat.
                with patch("random.randint", return_value=36):
                    self.session.combat.initiate_combat = MagicMock(return_value=(None, "No monster"))

                    self.session.simulate_step(context_bundle=None)

                    self.session.combat.initiate_combat.assert_called()

    def test_night_ambush_trigger(self):
        """Nighttime encounter should have chance to ambush."""
        monster_data = {"name": "Test Goblin", "ATK": 20, "level": 1, "tier": "Normal"}

        with patch("game_systems.adventure.adventure_session.WorldTime") as MockTime:
            MockTime.get_current_weather.return_value = Weather.CLEAR
            MockTime.get_current_phase.return_value = TimePhase.NIGHT
            MockTime.get_weather_flavor.return_value = "Clear Night"

            # Mock session context fetch
            with patch.object(self.session, "_fetch_session_context", return_value=self.mock_context):
                # Mock combat trigger
                with patch("random.randint", return_value=100):
                    # Mock initiate_combat
                    self.session.combat.initiate_combat = MagicMock(
                        return_value=(monster_data, "A wild goblin appears!")
                    )

                    # Mock random.random for Ambush (needs < 0.20)
                    with patch("random.random", return_value=0.10):
                        result = self.session.simulate_step(context_bundle=None)

                        # Verify Ambush Message
                        logs = "".join(result["sequence"][0])
                        self.assertIn("AMBUSH!", logs)

                        # Verify Damage (20 * 0.8 = 16)
                        expected_hp = 100 - 16
                        self.assertEqual(self.mock_context["vitals"]["current_hp"], expected_hp)
                        self.mock_db.set_player_vitals.assert_called_with(123456789, expected_hp, 50)

    def test_night_no_ambush(self):
        """Nighttime encounter chance failure should not ambush."""
        monster_data = {"name": "Test Goblin", "ATK": 20, "level": 1, "tier": "Normal"}

        with patch("game_systems.adventure.adventure_session.WorldTime") as MockTime:
            MockTime.get_current_weather.return_value = Weather.CLEAR
            MockTime.get_current_phase.return_value = TimePhase.NIGHT

            with patch.object(self.session, "_fetch_session_context", return_value=self.mock_context):
                with patch("random.randint", return_value=100):
                    self.session.combat.initiate_combat = MagicMock(
                        return_value=(monster_data, "A wild goblin appears!")
                    )

                    # Mock random.random > 0.20
                    with patch("random.random", return_value=0.50):
                        result = self.session.simulate_step(context_bundle=None)

                        logs = "".join(result["sequence"][0])
                        self.assertNotIn("AMBUSH!", logs)
                        self.assertEqual(self.mock_context["vitals"]["current_hp"], 100)

    def test_day_no_ambush(self):
        """Daytime encounter should never ambush."""
        monster_data = {"name": "Test Goblin", "ATK": 20, "level": 1, "tier": "Normal"}

        with patch("game_systems.adventure.adventure_session.WorldTime") as MockTime:
            MockTime.get_current_weather.return_value = Weather.CLEAR
            MockTime.get_current_phase.return_value = TimePhase.DAY

            with patch.object(self.session, "_fetch_session_context", return_value=self.mock_context):
                with patch("random.randint", return_value=100):
                    self.session.combat.initiate_combat = MagicMock(
                        return_value=(monster_data, "A wild goblin appears!")
                    )

                    # Even if random returns low value
                    with patch("random.random", return_value=0.10):
                        result = self.session.simulate_step(context_bundle=None)

                        logs = "".join(result["sequence"][0])
                        self.assertNotIn("AMBUSH!", logs)


if __name__ == "__main__":
    unittest.main()
