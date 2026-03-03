from unittest.mock import MagicMock, patch

import pytest

from game_systems.items.consumable_manager import ConsumableManager


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def manager(mock_db):
    return ConsumableManager(mock_db)


def test_triage_potency(manager, mock_db):
    discord_id = 123
    item_id = 1

    # Mock Item
    mock_db.get_inventory_item.return_value = {
        "item_key": "hp_potion_1",
        "item_type": "consumable",
        "count": 1,
    }

    # Mock Player Data (Base stats return HP as 50 + 10*10 = 150)
    mock_db.get_player_vitals.return_value = {
        "current_hp": 50,
        "current_mp": 50,
    }
    mock_db.get_player_stats_json.return_value = {
        "HP": 150,
        "MP": 100,
        "STR": 10,
        "END": 10,
        "DEX": 10,
        "AGI": 10,
        "MAG": 10,
        "LCK": 10,
    }

    # Mock Triage Skill (Level 1 = +20%)
    mock_db.get_player_skill_levels.return_value = {"triage": 1}

    # Base heal is 50
    # Expected Heal: 50 * (1.0 + 0.2) = 60

    with patch(
        "game_systems.items.consumable_manager.CONSUMABLES",
        {
            "hp_potion_1": {
                "effect": {"heal": 50},
                "name": "Potion",
                "type": "hp",
            }
        },
    ):
        with patch(
            "game_systems.items.consumable_manager.SKILLS",
            {
                "triage": {
                    "type": "Passive",
                    "passive_bonus": {"healing_item_potency": 0.2},
                }
            },
        ):
            mock_db.consume_item_atomic.return_value = True

            # Need to patch PlayerStats.from_dict because it calculates max_hp
            with patch("game_systems.items.consumable_manager.PlayerStats") as MockStats:
                mock_stats_instance = MagicMock()
                mock_stats_instance.max_hp = 150
                mock_stats_instance.max_mp = 100
                MockStats.from_dict.return_value = mock_stats_instance

                success, msg = manager.use_item(discord_id, item_id)

                assert success
                assert "60 HP" in msg
                assert "Boosted" in msg

                # Verify DB call
                mock_db.set_player_vitals.assert_called_with(discord_id, 110, 50)


def test_triage_potency_uncapped(manager, mock_db):
    discord_id = 123
    item_id = 1

    mock_db.get_inventory_item.return_value = {
        "item_key": "hp_potion_1",
        "item_type": "consumable",
        "count": 1,
    }

    mock_db.get_player_vitals.return_value = {
        "current_hp": 10,
        "current_mp": 50,
    }
    mock_db.get_player_skill_levels.return_value = {"triage": 1}

    with patch(
        "game_systems.items.consumable_manager.CONSUMABLES",
        {
            "hp_potion_1": {
                "effect": {"heal": 50},
                "name": "Potion",
                "type": "hp",
            }
        },
    ):
        with patch(
            "game_systems.items.consumable_manager.SKILLS",
            {
                "triage": {
                    "type": "Passive",
                    "passive_bonus": {"healing_item_potency": 0.2},
                }
            },
        ):
            mock_db.consume_item_atomic.return_value = True

            with patch("game_systems.items.consumable_manager.PlayerStats") as MockStats:
                mock_stats_instance = MagicMock()
                mock_stats_instance.max_hp = 150
                mock_stats_instance.max_mp = 100
                MockStats.from_dict.return_value = mock_stats_instance

                success, msg = manager.use_item(discord_id, item_id)

                # 50 * 1.2 = 60
                assert "60 HP" in msg
                mock_db.set_player_vitals.assert_called_with(discord_id, 70, 50)
