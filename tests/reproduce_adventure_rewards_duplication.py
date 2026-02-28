import os
import sys
from unittest.mock import MagicMock, patch

# Add root dir to sys.path
sys.path.append(os.getcwd())

# Mock modules before importing
sys.modules["pymongo"] = MagicMock()
sys.modules["pymongo.errors"] = MagicMock()
sys.modules["discord"] = MagicMock()

from game_systems.adventure.adventure_manager import AdventureManager


@patch("game_systems.adventure.adventure_manager.AdventureSession")
@patch("game_systems.adventure.adventure_manager.QuestSystem")
@patch("game_systems.adventure.adventure_manager.InventoryManager")
@patch("game_systems.adventure.adventure_manager.FactionSystem")
def test_end_adventure_duplicate_rewards_on_error(
    mock_faction, mock_inv, mock_quest, mock_session_cls
):
    """
    Reproduces the issue where rewards are granted multiple times if an error
    occurs during the end_adventure process (e.g., inside FactionSystem).
    """
    mock_db = MagicMock()
    mock_bot = MagicMock()

    manager = AdventureManager(mock_db, mock_bot)
    discord_id = 12345

    # 1. Setup Active Session
    mock_db.get_active_adventure.return_value = {
        "discord_id": discord_id,
        "location_id": "forest",
        "start_time": "2023-01-01T00:00:00",
        "end_time": "2023-01-01T01:00:00",
        "duration_minutes": 60,
        "active": 1,
        "status": "in_progress",
        "logs": "[]",
        "loot_collected": '{"exp": 100, "gold": 50}',
        "active_monster_json": None,
        "version": 1,
    }

    # Setup Lock Behavior (First call succeeds, subsequent calls fail)
    # This simulates atomic update: checks status != 'claiming'
    # First call: status is 'in_progress' -> Success (True)
    # Second call: status is 'claiming' (persisted from first) -> Fail (False)

    # We use a side_effect to simulate state change
    lock_state = {"locked": False}

    def lock_side_effect(did):
        if not lock_state["locked"]:
            lock_state["locked"] = True
            return True
        return False

    mock_db.lock_adventure_for_claiming.side_effect = lock_side_effect

    # Mock Session object
    mock_session = mock_session_cls.return_value
    mock_session.discord_id = discord_id
    mock_session.loot = {"exp": 100, "gold": 50}
    mock_session.active_monster = None

    # Mock Player Data
    mock_db.get_player.return_value = {
        "level": 1,
        "experience": 0,
        "exp_to_next": 1000,
        "current_hp": 100,
        "current_mp": 100,
        "aurum": 0,
    }
    mock_db.get_player_field.return_value = 1 # level

    mock_db.get_player_stats_json.return_value = {
        "strength": 10, "agility": 10, "intelligence": 10,
        "endurance": 10, "vitality": 10, "wisdom": 10,
        "max_hp": 100, "max_mp": 100
    }

    # Mock Inventory Manager success
    mock_inv.return_value.add_items_bulk.return_value = []

    # 2. Simulate Failure in Faction System (after rewards logic)
    mock_faction.return_value.grant_reputation_for_adventure.side_effect = Exception("DB Connection Lost")

    # 3. Execute First Attempt
    result1 = manager.end_adventure(discord_id)

    # Verify failure
    assert result1 is None # Should return None on exception

    # Verify Rewards were granted (Partial execution)
    # update_player_mixed is called to give XP
    mock_db.update_player_mixed.assert_called()
    assert mock_db.update_player_mixed.call_count == 1

    # Verify Lock was attempted
    mock_db.lock_adventure_for_claiming.assert_called()

    # verify session was NOT ended (normally called at the very end)
    mock_db.end_adventure_session.assert_not_called()

    # 4. Execute Second Attempt (User retries)
    # The lock is still held (lock_state["locked"] is True)
    # So this call should fail early.

    # Re-setup the session mock (though it shouldn't be reached)
    mock_session.loot = {"exp": 100, "gold": 50}

    # Even if Faction System is fixed now
    mock_faction.return_value.grant_reputation_for_adventure.side_effect = None
    mock_faction.return_value.grant_reputation_for_adventure.return_value = ["Reputation +10"]

    result2 = manager.end_adventure(discord_id)

    # Verify result is None (Blocked by lock)
    assert result2 is None

    # Verify Rewards were NOT granted AGAIN (Call count remains 1)
    assert mock_db.update_player_mixed.call_count == 1

    # Session still not ended via end_adventure_session (requires admin intervention or timeout logic, but prevents dupes)
    mock_db.end_adventure_session.assert_not_called()

    print("\nTest passed: Duplicate rewards prevented by locking.")
