import sys
from unittest.mock import MagicMock, patch

# --- MOCK PYMONGO ---
sys.modules["pymongo"] = MagicMock()
sys.modules["pymongo.errors"] = MagicMock()
sys.modules["pymongo.collection"] = MagicMock()
sys.modules["pymongo.database"] = MagicMock()

import pytest

from game_systems.adventure.adventure_rewards import AdventureRewards
from game_systems.adventure.event_handler import EventHandler
from game_systems.events.world_event_system import WorldEventSystem
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


def test_builders_boon_event_config(mock_db):
    """Verify WorldEventSystem loads Builder's Boon modifiers correctly."""
    system = WorldEventSystem(mock_db)

    # Mock active event in DB
    mock_db.get_active_world_event.return_value = {
        "type": "builders_boon",
        "end_time": "2099-12-31T23:59:59",
    }

    event = system.get_current_event()
    modifiers = system.get_modifiers()

    assert event["name"] == "The Builder's Boon"
    assert modifiers["builder_boost"] == 3.0
    assert modifiers["aurum_boost"] == 1.5


def test_builders_boon_gathering_multiplier(mock_db, mock_quest_system):
    """Verify EventHandler applies builder_boost to specific materials."""
    event_handler = EventHandler(mock_db, mock_quest_system, 12345)

    mock_context = {
        "player_stats": PlayerStats(),
        "active_boosts": {
            "builder_boost": 3.0,
            "gathering_boost": 1.0,
        },
    }

    with (
        patch("random.randint", return_value=1),
        patch("random.choices", return_value=["ancient_wood"]),
        patch("random.random", return_value=0.5),
        patch("game_systems.data.materials.MATERIALS", {"ancient_wood": {"name": "Ancient Wood"}}),
    ):
        result = event_handler._perform_wild_gathering(mock_context, location_id="test_loc")
        # Without boost, quantity is 1 (luck=0). With builder_boost=3.0, quantity = 1 * 3 = 3
        assert "log" in result
        assert "Ancient Wood (x3)" in result["log"][0]
        assert "(Bonus)" in result["log"][0]


def test_builders_boon_gathering_multiplier_ignores_other_items(mock_db, mock_quest_system):
    """Verify EventHandler ignores builder_boost for non-building materials."""
    event_handler = EventHandler(mock_db, mock_quest_system, 12345)

    mock_context = {
        "player_stats": PlayerStats(),
        "active_boosts": {
            "builder_boost": 3.0,
            "gathering_boost": 1.0,
        },
    }

    with (
        patch("random.randint", return_value=1),
        patch("random.choices", return_value=["medicinal_herb"]),
        patch("random.random", return_value=0.5),
        patch("game_systems.data.materials.MATERIALS", {"medicinal_herb": {"name": "Medicinal Herb"}}),
    ):
        result = event_handler._perform_wild_gathering(mock_context, location_id="test_loc")
        # Without boost, quantity is 1
        assert "log" in result
        assert "Medicinal Herb" in result["log"][0]
        assert "x3" not in result["log"][0]


def test_builders_boon_aurum_multiplier(mock_db):
    """Verify AdventureRewards multiplies combat aurum by aurum_boost."""
    rewards = AdventureRewards(mock_db, 12345)

    combat_result = {
        "exp": 100,
        "aurum": 50,
        "monster_data": {"name": "Golem", "tier": "Normal"},
        "active_boosts": {
            "aurum_boost": 1.5,
        },
    }

    session_loot = {}

    with patch(
        "game_systems.rewards.loot_calculator.LootCalculator.roll_drops",
        return_value=[],
    ):
        rewards._process_loot_and_quests(
            combat_result,
            MagicMock(),
            MagicMock(),
            session_loot,
            [],
        )

        # Aurum should be 50 * 1.5 = 75
        assert session_loot["aurum"] == 75
