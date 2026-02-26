
import sys
from unittest.mock import MagicMock, patch

import pytest

# Mock modules before importing
sys.modules["pymongo"] = MagicMock()
sys.modules["pymongo.errors"] = MagicMock()
sys.modules["discord"] = MagicMock()

from game_systems.adventure.adventure_resolution import AdventureResolutionEngine  # noqa: E402
from game_systems.adventure.adventure_session import AdventureSession  # noqa: E402
from game_systems.player.player_stats import PlayerStats  # noqa: E402


@pytest.fixture
def mock_db():
    db = MagicMock()
    # Setup common db returns
    db.get_active_boosts.return_value = []
    db.get_active_world_event.return_value = None
    return db


@pytest.fixture
def mock_combat_handler():
    with patch("game_systems.adventure.adventure_session.CombatHandler") as mock_cls:
        handler = mock_cls.return_value
        yield handler


@pytest.fixture
def mock_event_handler():
    with patch("game_systems.adventure.adventure_session.EventHandler") as mock_cls:
        handler = mock_cls.return_value
        yield handler


@pytest.fixture
def mock_rewards():
    with patch("game_systems.adventure.adventure_session.AdventureRewards") as mock_cls:
        rewards = mock_cls.return_value
        yield rewards


def test_full_adventure_success(mock_db, mock_combat_handler, mock_event_handler, mock_rewards):
    """
    Simulates a successful 2-hour adventure (8 steps).
    Verifies that steps are executed, loot is accumulated, and session completes.
    """
    # Setup Mocks
    engine = AdventureResolutionEngine(MagicMock(), mock_db)

    # Mock player context
    mock_db.get_combat_context_bundle.return_value = {
        "stats": {"HP": 100, "MP": 50},
        "buffs": [],
        "player": {"current_hp": 100, "current_mp": 50, "level": 10},
        "skills": {},
    }

    # Mock Combat: Always success
    monster_data = {"name": "Test Monster", "level": 5, "ATK": 10, "DEF": 5, "HP": 50, "xp": 100}
    mock_combat_handler.initiate_combat.return_value = (monster_data, "A monster appears!")
    mock_combat_handler.create_empty_battle_report.return_value = {}

    # Mock Resolve Turn: Player wins
    mock_combat_handler.resolve_turn.return_value = {
        "winner": "player",
        "hp_current": 90,
        "mp_current": 40,
        "phrases": ["You hit mock monster!"],
        "turn_report": {},
        "monster_data": monster_data
    }

    # Mock Rewards processing
    mock_rewards.process_victory.return_value = ["You gained 100 XP and loot."]

    # Session Doc: 2 hours = 8 steps
    session_doc = {
        "discord_id": 12345,
        "location_id": "forest_outskirts",
        "duration_minutes": 120,
        "steps_completed": 0,
        "active": 1,
        "logs": "[]",
        "loot_collected": "{}",
        "active_monster_json": None,
        "supplies": {},
    }

    # Execute
    result = engine.resolve_session(session_doc)

    # Verify
    assert result is True
    assert mock_db.update_adventure_status.call_args[0] == (12345, "completed")
    assert mock_db.update_adventure_session.called
    assert mock_rewards.process_victory.called


def test_fatigue_scaling(mock_db, mock_combat_handler, mock_event_handler, mock_rewards):
    """
    Verifies that fatigue multiplier increases correctly after 4 hours (16 steps).
    """
    engine = AdventureResolutionEngine(MagicMock(), mock_db)

    # Mock player context
    mock_db.get_combat_context_bundle.return_value = {
        "stats": {"HP": 100, "MP": 50},
        "buffs": [],
        "player": {"current_hp": 100, "current_mp": 50, "level": 10},
        "skills": {},
    }

    # Mock Combat to capture fatigue_multiplier
    monster_data = {"name": "Fatigue Monster", "level": 5, "ATK": 10, "DEF": 5, "HP": 50, "xp": 100}
    mock_combat_handler.initiate_combat.return_value = (monster_data, "A monster appears!")
    mock_combat_handler.create_empty_battle_report.return_value = {}

    captured_fatigue = []

    def side_effect_resolve(*args, **kwargs):
        fm = kwargs.get("fatigue_multiplier", 1.0)
        captured_fatigue.append(fm)
        return {
            "winner": "player",
            "hp_current": 100,
            "mp_current": 50,
            "phrases": ["Hit!"],
            "turn_report": {},
            "monster_data": monster_data
        }

    mock_combat_handler.resolve_turn.side_effect = side_effect_resolve

    # Session Doc: 6 hours = 24 steps
    # Fatigue starts > 16 steps (4 hours)
    session_doc = {
        "discord_id": 999,
        "location_id": "forest_outskirts",
        "duration_minutes": 360, # 6 hours
        "steps_completed": 0,
        "active": 1,
        "logs": "[]",
        "loot_collected": "{}",
        "active_monster_json": None,
        "supplies": {},
    }

    # Force combat every step to capture fatigue
    # We patch randint to 100 to ensure encounter triggers
    with patch("random.randint", return_value=100):
        engine.resolve_session(session_doc)

    # Verify Fatigue
    # Note: Adventure rhythm is Encounter -> Combat -> Encounter -> Combat...
    # Combat happens on steps 2, 4, 6, 8, 10, 12, 14, 16, 18, 20...
    # So captured_fatigue indices correspond to these steps.

    # Indices 0-7 (Steps 2-16): Should be 1.0
    # Index 8 (Step 18): Should be > 1.0 (17-16)/4 * 0.05 = 0.0125 -> 1.0125

    assert len(captured_fatigue) > 0

    # Check safe period (Steps <= 16)
    # 8 combat encounters expected in first 16 steps
    safe_encounters = 8
    for i in range(safe_encounters):
        if i < len(captured_fatigue):
            assert captured_fatigue[i] == 1.0, f"Combat {i+1} (Step {(i+1)*2}) fatigue should be 1.0"

    # Check fatigue period
    if len(captured_fatigue) > safe_encounters:
        # Index 8 is Step 18
        # Fatigue = (17 - 16)/4 * 0.05 + 1.0 = 1.0125
        assert abs(captured_fatigue[8] - 1.0125) < 0.001, f"Combat 9 (Step 18) fatigue should be 1.0125, got {captured_fatigue[8]}"


def test_player_death_handling(mock_db, mock_combat_handler, mock_event_handler, mock_rewards):
    """
    Verifies that the session terminates early on player death.
    """
    engine = AdventureResolutionEngine(MagicMock(), mock_db)

    # Mock player context
    mock_db.get_combat_context_bundle.return_value = {
        "stats": {"HP": 100, "MP": 50},
        "buffs": [],
        "player": {"current_hp": 100, "current_mp": 50, "level": 10},
        "skills": {},
    }

    monster_data = {"name": "Killer Monster", "level": 50, "ATK": 100, "DEF": 50, "HP": 500}
    mock_combat_handler.initiate_combat.return_value = (monster_data, "A killer appears!")
    mock_combat_handler.create_empty_battle_report.return_value = {}

    # Ensure rewards return a list (so JSON serialization doesn't fail)
    mock_rewards.process_victory.return_value = []

    # First combat: Player wins
    # Second combat: Player dies
    # Note: Because of Encounter->Combat rhythm, Combat happens at Step 2 and Step 4.

    def side_effect_death(*args, **kwargs):
        call_count = mock_combat_handler.resolve_turn.call_count

        # First call (Step 2)
        if call_count == 1:
            return {
                "winner": "player",
                "hp_current": 50,
                "mp_current": 40,
                "phrases": ["Win"],
                "turn_report": {},
                "monster_data": monster_data
            }
        # Second call (Step 4)
        else:
            return {
                "winner": "monster", # Dies
                "hp_current": 0,
                "mp_current": 0,
                "phrases": ["Dead"],
                "turn_report": {},
                "monster_data": monster_data
            }

    mock_combat_handler.resolve_turn.side_effect = side_effect_death

    session_doc = {
        "discord_id": 666,
        "location_id": "forest_outskirts",
        "duration_minutes": 60, # 4 steps
        "steps_completed": 0,
        "active": 1,
        "logs": "[]",
        "loot_collected": "{}",
        "active_monster_json": None,
        "supplies": {},
    }

    # Force combat
    with patch("random.randint", return_value=100):
        result = engine.resolve_session(session_doc)

    assert result is True
    # Should be failed
    assert mock_db.update_adventure_status.call_args[0] == (666, "failed")
    # Should have called handle_death (which updates vitals delta)
    assert mock_db.update_player_vitals_delta.called
