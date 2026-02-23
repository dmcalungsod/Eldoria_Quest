
import json
import sys
import os
from unittest.mock import MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock discord
sys.modules["discord"] = MagicMock()
sys.modules["discord.ui"] = MagicMock()
sys.modules["discord.ext"] = MagicMock()
sys.modules["pymongo"] = MagicMock()
sys.modules["pymongo.errors"] = MagicMock()

import pytest
from game_systems.adventure.ui.adventure_embeds import AdventureEmbeds
from game_systems.data.adventure_locations import LOCATIONS

@pytest.fixture(autouse=True)
def reset_discord_mock():
    # Create a fresh mock for Embed each test
    sys.modules["discord"].Embed.side_effect = lambda **kwargs: MagicMock()

def test_build_status_embed_with_stance():
    # Mock data
    session = {
        "location_id": "forest_clearing",
        "end_time": "2023-01-01T12:00:00",
        "steps_completed": 5,
        "loot_collected": "{}",
        "logs": "[]",
        "active_monster_json": json.dumps({
            "name": "Goblin",
            "HP": 50,
            "max_hp": 50,
            "player_stance": "aggressive"
        })
    }
    location_data = {"name": "Forest", "emoji": "🌲"}

    # Call method
    embed = AdventureEmbeds.build_status_embed(session, location_data, "10m", 5)

    # Verify Stance Field via Mock calls
    found = False
    for call in embed.add_field.call_args_list:
        # call is tuple(args, kwargs) if inspecting directly, or call object
        # With MagicMock, accessing .kwargs works
        if call.kwargs.get("name") == "⚔️ Tactics":
            found = True
            val = call.kwargs.get("value")
            assert "⚔️ **Aggressive**" in val
            assert "High Dmg" in val
            break

    assert found, "Tactics field not added"

def test_build_status_embed_without_monster():
    # Mock data
    session = {
        "location_id": "forest_clearing",
        "active_monster_json": None
    }
    location_data = {"name": "Forest", "emoji": "🌲"}

    # Call method
    embed = AdventureEmbeds.build_status_embed(session, location_data, "10m", 5)

    # Verify No Stance Field
    found = False
    for call in embed.add_field.call_args_list:
        if call.kwargs.get("name") == "⚔️ Tactics":
            found = True
            break
    assert not found

def test_build_status_embed_default_stance():
    # Mock data
    session = {
        "location_id": "forest_clearing",
        "active_monster_json": json.dumps({
            "name": "Goblin",
            "HP": 50,
            "max_hp": 50
            # No player_stance key
        })
    }
    location_data = {"name": "Forest", "emoji": "🌲"}

    # Call method
    embed = AdventureEmbeds.build_status_embed(session, location_data, "10m", 5)

    # Verify Stance Field defaults to balanced
    found = False
    for call in embed.add_field.call_args_list:
        if call.kwargs.get("name") == "⚔️ Tactics":
            found = True
            val = call.kwargs.get("value")
            assert "⚖️ **Balanced**" in val
            break

    assert found, "Tactics field not added"
