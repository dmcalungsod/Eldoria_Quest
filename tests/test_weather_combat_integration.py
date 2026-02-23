import pytest
from unittest.mock import MagicMock, patch
import sys
import os

# Add repo root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock modules before importing
sys.modules["pymongo"] = MagicMock()
sys.modules["pymongo.errors"] = MagicMock()
sys.modules["discord"] = MagicMock()

from game_systems.adventure.adventure_session import AdventureSession
from game_systems.world_time import Weather, WorldTime
from game_systems.player.player_stats import PlayerStats


@pytest.fixture
def mock_db():
    db = MagicMock()
    # Mock player stats with CORRECT KEYS
    stats_dict = {
        "STR": {"base": 10, "bonus": 0},
        "END": {"base": 10, "bonus": 0},
        "DEX": {"base": 10, "bonus": 0},
        "AGI": {"base": 10, "bonus": 0},
        "MAG": {"base": 10, "bonus": 0},
        "LCK": {"base": 10, "bonus": 0},
    }
    db.get_player_stats_json.return_value = stats_dict

    # Mock player vitals and other context needed by _fetch_session_context
    db.get_combat_context_bundle.return_value = {
        "stats": stats_dict,
        "player": {
            "current_hp": 100,
            "current_mp": 50,
            "class_id": 1,
            "level": 1,
            "experience": 0,
            "exp_to_next": 100,
        },
        "skills": [],
        "buffs": [],  # Empty buffs list
    }
    db.get_active_boosts.return_value = []
    # Mock world event to be None to avoid fromisoformat error in WorldEventSystem
    db.get_active_world_event.return_value = None

    return db


@pytest.fixture
def session(mock_db):
    quest_system = MagicMock()
    inventory_manager = MagicMock()
    # Use a real location ID found in LOCATIONS, or patch LOCATIONS in the test itself
    # "forest_outskirts" is a standard location
    s = AdventureSession(mock_db, quest_system, inventory_manager, 12345)
    s.location_id = "forest_outskirts"
    s.active = True
    return s


class TestWeatherCombatIntegration:

    @patch("game_systems.adventure.adventure_session.WorldTime.get_current_weather")
    def test_apply_weather_effects_rain(self, mock_weather, session):
        """Test that Rain reduces Agility by 10%."""
        mock_weather.return_value = Weather.RAIN

        # Simulate fetching context (normally done in simulate_step)
        context = session._fetch_session_context()
        assert context is not None, "Context should not be None"

        logs = session._apply_weather_effects(context, Weather.RAIN)

        # Verify Stats
        stats = context["player_stats"]
        # Base AGI 10 -> -10% = -1
        # Total AGI should be 9
        assert stats.agility == 9
        assert stats._stats["AGI"].bonus == -1

        # Verify Logs (case insensitive check for 'rain')
        assert any("rain" in log.lower() and "AGI" in log for log in logs)

    @patch("game_systems.adventure.adventure_session.WorldTime.get_current_weather")
    def test_apply_weather_effects_storm(self, mock_weather, session):
        """Test that Storm increases Magic by 10%."""
        mock_weather.return_value = Weather.STORM

        context = session._fetch_session_context()
        assert context is not None

        logs = session._apply_weather_effects(context, Weather.STORM)

        stats = context["player_stats"]
        # Base MAG 10 -> +10% = +1
        assert stats.magic == 11
        assert stats._stats["MAG"].bonus == 1

        assert any("storm" in log.lower() and "MAG" in log for log in logs)

    @patch("game_systems.adventure.adventure_session.WorldTime.get_current_weather")
    def test_simulate_step_integration_exploration(self, mock_weather, session):
        """Test that simulate_step includes weather log during exploration."""
        mock_weather.return_value = Weather.RAIN

        # Ensure location is valid in LOCATIONS
        with patch(
            "game_systems.adventure.adventure_session.LOCATIONS",
            {"forest_outskirts": {"name": "Forest", "monsters": [], "gatherables": []}},
        ):
            # Mock combat.initiate_combat to trigger an encounter
            session.combat = MagicMock()
            session.combat.initiate_combat.return_value = (
                {"name": "Goblin"},
                "A wild Goblin appears!",
            )

            # Mock events
            session.events = MagicMock()

            # Force combat trigger (regen_threshold logic)
            with patch("random.randint", return_value=100):
                result = session.simulate_step(context_bundle=None)

                frames = result["sequence"]
                assert len(frames) > 0
                first_frame_text = frames[0][0]

                # The log should contain the weather effect description
                assert "rain" in first_frame_text.lower()
                assert "slippery" in first_frame_text.lower()
                assert "Goblin" in first_frame_text

    @patch("game_systems.adventure.adventure_session.WorldTime.get_current_weather")
    def test_simulate_step_integration_active_combat(self, mock_weather, session):
        """Test that simulate_step suppresses weather log during active combat."""
        mock_weather.return_value = Weather.RAIN

        # Ensure location is valid
        with patch(
            "game_systems.adventure.adventure_session.LOCATIONS",
            {"forest_outskirts": {"name": "Forest"}},
        ):
            # Set active monster
            session.active_monster = {"name": "Goblin", "HP": 50}

            # Disable auto-combat by mocking _check_auto_condition to False
            session._check_auto_condition = MagicMock(return_value=False)

            # Mock _process_combat_turn
            session._process_combat_turn = MagicMock()
            session._process_combat_turn.return_value = {
                "sequence": [["Combat continues..."]],
                "dead": False,
            }

            session.simulate_step(context_bundle=None)

            # Verify _process_combat_turn was called
            args, kwargs = session._process_combat_turn.call_args
            context_arg = args[0]
            prepend_logs_arg = kwargs.get("prepend_logs")

            # Check context has modifiers (Agility reduced)
            assert context_arg["player_stats"].agility == 9

            # Check logs suppressed (prepend_logs should be None or not contain weather info)
            assert not prepend_logs_arg or "Rain" not in str(prepend_logs_arg)
