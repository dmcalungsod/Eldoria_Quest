"""
tests/test_event_frostfall.py

Tests specifically for "The Frostfall Expedition" event.
Verifies:
1. Event configuration and modifiers.
2. Threat reduction in Frostfall Expanse.
3. Loot bonuses in Frostfall Expanse.
"""

import sys
from unittest.mock import MagicMock, patch

# --- MOCK PYMONGO ---
# This must be done BEFORE importing any module that uses DatabaseManager
sys.modules["pymongo"] = MagicMock()
sys.modules["pymongo.errors"] = MagicMock()
sys.modules["pymongo.collection"] = MagicMock()
sys.modules["pymongo.database"] = MagicMock()

import pytest
from game_systems.events.world_event_system import WorldEventSystem
from game_systems.adventure.adventure_session import AdventureSession
from game_systems.adventure.adventure_rewards import AdventureRewards
from game_systems.player.player_stats import PlayerStats

@pytest.fixture
def mock_db():
    return MagicMock()

@pytest.fixture
def mock_quest_system():
    return MagicMock()

@pytest.fixture
def mock_inventory_manager():
    return MagicMock()

def test_event_config(mock_db):
    """Verify WorldEventSystem loads Frostfall Expedition modifiers correctly."""
    system = WorldEventSystem(mock_db)

    # Mock active event in DB
    mock_db.get_active_world_event.return_value = {
        "type": "frostfall_expedition",
        "end_time": "2099-12-31T23:59:59"
    }

    event = system.get_current_event()
    modifiers = system.get_modifiers()

    assert event["name"] == "The Frostfall Expedition"
    assert modifiers["frostfall_threat_reduction"] == 0.9
    assert modifiers["frostfall_loot_bonus"] == 1.5
    assert modifiers["loot_boost"] == 1.25

def test_adventure_session_threat_reduction(mock_db, mock_quest_system, mock_inventory_manager):
    """Verify AdventureSession applies threat reduction in Frostfall."""
    # Setup Session
    session = AdventureSession(mock_db, mock_quest_system, mock_inventory_manager, 12345)
    session.location_id = "frostfall_expanse"
    session.active_monster = {"name": "Ice Wolf", "tier": "Normal", "level": 10, "ATK": 20}
    session.version = 1

    # Mock Context with Event Modifiers
    mock_context = {
        "player_stats": PlayerStats(),
        "stats_dict": {"HP": 100, "MP": 50},
        "vitals": {"current_hp": 100, "current_mp": 50},
        "player_row": {"level": 10},
        "active_boosts": {
            "frostfall_threat_reduction": 0.5, # Exaggerated for testing (50% reduction)
        },
        "event_type": "frostfall_expedition"
    }

    # Mock Combat Handler
    session.combat = MagicMock()
    # We want to intercept the call to resolve_turn to check the fatigue_multiplier
    # resolve_turn(monster, report, xp, context, action, stance, persist, fatigue_multiplier, ...)

    session.combat.create_empty_battle_report.return_value = {}
    session.combat.resolve_turn.return_value = {
        "phrases": ["Combat happens."],
        "hp_current": 100,
        "mp_current": 50,
        "winner": None
    }

    # Mock fetch_session_context to return our mock
    with patch.object(session, '_fetch_session_context', return_value=mock_context):
        # Run simulate_step
        session.simulate_step(action="attack")

        # Verify resolve_turn was called with reduced multiplier
        # Default fatigue is 1.0. With 0.5 modifier, passed multiplier should be 0.5.
        args, kwargs = session.combat.resolve_turn.call_args

        # Check kwargs for fatigue_multiplier
        assert kwargs["fatigue_multiplier"] == 0.5

def test_adventure_session_no_reduction_elsewhere(mock_db, mock_quest_system, mock_inventory_manager):
    """Verify threat reduction is NOT applied outside Frostfall."""
    session = AdventureSession(mock_db, mock_quest_system, mock_inventory_manager, 12345)
    session.location_id = "forest_outskirts" # NOT Frostfall
    session.active_monster = {"name": "Wolf", "tier": "Normal"}

    # Fix: Ensure mock_context has "current_mp" in "vitals"
    mock_context = {
        "player_stats": PlayerStats(),
        "stats_dict": {"HP": 100},
        "vitals": {"current_hp": 100, "current_mp": 50}, # Added current_mp
        "player_row": {"level": 10},
        "active_boosts": {
            "frostfall_threat_reduction": 0.5,
        },
        "event_type": "frostfall_expedition"
    }

    session.combat = MagicMock()
    session.combat.create_empty_battle_report.return_value = {}
    session.combat.resolve_turn.return_value = {"phrases": [], "winner": None, "hp_current": 100, "mp_current": 50}

    with patch.object(session, '_fetch_session_context', return_value=mock_context):
        session.simulate_step(action="attack")

        # Ensure simulate_step didn't crash
        assert session.combat.resolve_turn.called

        args, kwargs = session.combat.resolve_turn.call_args
        # Should be 1.0 (standard)
        assert kwargs["fatigue_multiplier"] == 1.0

def test_adventure_rewards_loot_bonus(mock_db, mock_inventory_manager):
    """Verify loot bonus is applied in Frostfall."""
    rewards = AdventureRewards(mock_db, 12345)

    # Mock Inputs
    combat_result = {
        "exp": 100,
        "drops": ["ice_shard"],
        "monster_data": {"name": "Ice Wolf", "tier": "Normal"},
        "active_boosts": {
            "loot_boost": 1.0,
            "frostfall_loot_bonus": 2.0 # 2x Loot
        }
    }

    # Mock LootCalculator to track the boost it receives
    with patch('game_systems.rewards.loot_calculator.LootCalculator.roll_drops', return_value=[]) as mock_roll:
        # Act
        rewards._process_loot_and_quests(
            combat_result,
            MagicMock(),
            mock_inventory_manager,
            {},
            [],
            location_id="frostfall_expanse"
        )

        # Assert: roll_drops(drops, luck, loot_boost)
        # loot_boost should be 1.0 * 2.0 = 2.0
        args, _ = mock_roll.call_args
        passed_boost = args[2]
        assert passed_boost == 2.0

def test_adventure_rewards_no_bonus_elsewhere(mock_db, mock_inventory_manager):
    """Verify loot bonus is NOT applied outside Frostfall."""
    rewards = AdventureRewards(mock_db, 12345)

    combat_result = {
        "exp": 100,
        "drops": [],
        "monster_data": {"name": "Wolf"},
        "active_boosts": {
            "loot_boost": 1.0,
            "frostfall_loot_bonus": 2.0
        }
    }

    with patch('game_systems.rewards.loot_calculator.LootCalculator.roll_drops', return_value=[]) as mock_roll:
        rewards._process_loot_and_quests(
            combat_result,
            MagicMock(),
            mock_inventory_manager,
            {},
            [],
            location_id="forest_outskirts" # Wrong location
        )

        args, _ = mock_roll.call_args
        passed_boost = args[2]
        assert passed_boost == 1.0
