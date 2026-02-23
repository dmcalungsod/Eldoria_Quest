import sys
from unittest.mock import MagicMock, patch

import pytest

# Mock modules before importing
sys.modules["pymongo"] = MagicMock()
sys.modules["pymongo.errors"] = MagicMock()
sys.modules["discord"] = MagicMock()

from game_systems.adventure.adventure_resolution import AdventureResolutionEngine  # noqa: E402


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def mock_bot():
    return MagicMock()


@patch("game_systems.adventure.adventure_resolution.AdventureSession")
@patch("game_systems.adventure.adventure_resolution.QuestSystem")
@patch("game_systems.adventure.adventure_resolution.InventoryManager")
@patch("game_systems.adventure.adventure_resolution.AdventureManager")
def test_resolution_success(mock_mgr, mock_inv, mock_quest, mock_session_cls, mock_bot, mock_db):
    # Setup
    engine = AdventureResolutionEngine(mock_bot, mock_db)

    mock_session = mock_session_cls.return_value
    mock_session.steps_completed = 0
    # Simulate step returns success (not dead)
    mock_session.simulate_step.return_value = {"dead": False}

    session_doc = {
        "discord_id": 123,
        "duration_minutes": 30,  # 2 steps
        "steps_completed": 0,
    }

    # Execute
    result = engine.resolve_session(session_doc)

    # Verify
    assert result is True
    # Should create session
    mock_session_cls.assert_called_once()
    # Should simulate 2 steps (30 / 15)
    assert mock_session.simulate_step.call_count == 2
    mock_session.simulate_step.assert_called_with(background=True)
    # Should save state 2 times
    assert mock_session.save_state.call_count == 2
    # Should update status to completed
    mock_db.update_adventure_status.assert_called_with(123, "completed")


@patch("game_systems.adventure.adventure_resolution.AdventureSession")
@patch("game_systems.adventure.adventure_resolution.QuestSystem")
@patch("game_systems.adventure.adventure_resolution.InventoryManager")
@patch("game_systems.adventure.adventure_resolution.AdventureManager")
def test_resolution_death(mock_mgr, mock_inv, mock_quest, mock_session_cls, mock_bot, mock_db):
    # Setup
    engine = AdventureResolutionEngine(mock_bot, mock_db)

    mock_session = mock_session_cls.return_value
    mock_session.steps_completed = 0
    mock_session.logs = []
    mock_session.loot = {}
    mock_session.version = 1

    # First step ok, second step dead
    mock_session.simulate_step.side_effect = [{"dead": False}, {"dead": True}]

    # Mock death handler return
    mock_mgr.return_value._handle_death_rewards.return_value = "You died."

    session_doc = {
        "discord_id": 123,
        "duration_minutes": 45,  # 3 steps
        "steps_completed": 0,
    }

    # Execute
    result = engine.resolve_session(session_doc)

    # Verify
    assert result is True
    # Should simulate 2 steps only
    assert mock_session.simulate_step.call_count == 2
    # Should handle death
    engine.adventure_manager._handle_death_rewards.assert_called_once_with(123, mock_session)
    # Should update status to failed
    mock_db.update_adventure_status.assert_called_with(123, "failed")


@patch("game_systems.adventure.adventure_resolution.AdventureSession")
@patch("game_systems.adventure.adventure_resolution.QuestSystem")
@patch("game_systems.adventure.adventure_resolution.InventoryManager")
@patch("game_systems.adventure.adventure_resolution.AdventureManager")
def test_resume_session(mock_mgr, mock_inv, mock_quest, mock_session_cls, mock_bot, mock_db):
    # Setup
    engine = AdventureResolutionEngine(mock_bot, mock_db)

    mock_session = mock_session_cls.return_value
    # Resuming from step 2 of 4
    mock_session.steps_completed = 2
    mock_session.simulate_step.return_value = {"dead": False}

    session_doc = {
        "discord_id": 123,
        "duration_minutes": 60,  # 4 steps total
        "steps_completed": 2,
    }

    # Execute
    engine.resolve_session(session_doc)

    # Verify
    # Should simulate remaining 2 steps
    assert mock_session.simulate_step.call_count == 2
    mock_db.update_adventure_status.assert_called_with(123, "completed")
