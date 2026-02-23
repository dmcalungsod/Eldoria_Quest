import sys
from unittest.mock import MagicMock

# --- MODULE LEVEL PATCHING ---
# Patch pymongo and discord BEFORE importing production code
sys.modules["pymongo"] = MagicMock()
sys.modules["pymongo.errors"] = MagicMock()
sys.modules["discord"] = MagicMock()
# -----------------------------

import pytest  # noqa: E402
from game_systems.items.equipment_manager import EquipmentManager  # noqa: E402
from game_systems.player.player_stats import PlayerStats  # noqa: E402


@pytest.fixture
def mock_db():
    db = MagicMock()
    # Mock player stats JSON
    # IMPORTANT: Use .get() structure matching what code expects
    db.get_player_stats_json.return_value = {
        "STR": {"base": 10, "bonus": 0},
        "END": {"base": 10, "bonus": 0},
    }
    db.get_player_vitals.return_value = {"current_hp": 100, "current_mp": 50}
    db.get_all_player_skills.return_value = []

    # Mock _col for find_one lookups
    def mock_find_one(query, projection=None):
        if "id" in query:
            if query["id"] == 1:
                return {
                    "id": 1,
                    "name": "Valid Sword",
                    "str_bonus": 5,
                    "rarity": "Common",
                }
            elif query["id"] == 2:
                return {
                    "id": 2,
                    "name": "Valid Shield",
                    "end_bonus": 5,
                    "rarity": "Common",
                }
        return None

    db._col.return_value.find_one.side_effect = mock_find_one
    db.get_equipped_items.return_value = []

    return db


def test_recalculate_robustness(mock_db):
    """
    Test that recalculate_player_stats handles invalid item keys gracefully
    without crashing or discarding valid item bonuses.
    """
    mgr = EquipmentManager(mock_db)
    discord_id = 12345

    # Setup equipped items: One valid, one with non-numeric key
    mock_db.get_equipped_items.return_value = [
        {
            "id": 101,
            "item_key": "1",
            "item_source_table": "equipment",
            "rarity": "Common",
        },
        {
            "id": 102,
            "item_key": "bad_key_sword",
            "item_source_table": "equipment",
            "rarity": "Common",
        },
    ]

    # Run calculation
    # This should log error but return stats with valid bonuses applied
    stats = mgr.recalculate_player_stats(discord_id)

    # Assertions
    # 1. Base stats should be preserved (10)
    # 2. Valid item bonus should be applied (+5 STR)
    # 3. Invalid item should be ignored (no crash)

    # If the function crashed inside the loop, it would return default stats (base 1)
    # If it processed successfully, it would have base 10 + bonus 5 = 15

    # Currently, we expect it to FAIL (return default stats) because of the crash.
    # So assertions should fail if the code is buggy.

    assert stats.strength == 15, "Should have 10 base + 5 bonus from valid item"
    assert stats.endurance == 10, "Should have 10 base + 0 bonus"

    # Verify update was called with the correct stats
    mock_db.update_player_stats.assert_called_once()
    saved_stats = mock_db.update_player_stats.call_args[0][1]
    assert saved_stats["STR"]["bonus"] == 5


def test_recalculate_missing_item(mock_db):
    """Test handling of items that are numeric but missing in DB."""
    mgr = EquipmentManager(mock_db)
    discord_id = 12345

    mock_db.get_equipped_items.return_value = [
        {
            "id": 103,
            "item_key": "999",  # Non-existent ID
            "item_source_table": "equipment",
            "rarity": "Common",
        }
    ]

    stats = mgr.recalculate_player_stats(discord_id)

    assert stats.strength == 10  # Base only
    mock_db.update_player_stats.assert_called_once()
