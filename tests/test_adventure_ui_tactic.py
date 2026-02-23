
import json
import os
import sys
from unittest.mock import MagicMock

# --- Global Module Patching (Must happen before imports) ---
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock discord and pymongo to prevent ImportErrors during module loading
sys.modules["discord"] = MagicMock()
sys.modules["discord.ui"] = MagicMock()
sys.modules["discord.ext"] = MagicMock()
sys.modules["pymongo"] = MagicMock()
sys.modules["pymongo.errors"] = MagicMock()
# -----------------------------------------------------------

from unittest.mock import patch  # noqa: E402

import pytest  # noqa: E402

from game_systems.adventure.ui.adventure_embeds import AdventureEmbeds  # noqa: E402


@pytest.fixture
def mock_discord_embed():
    """
    Patches discord.Embed inside AdventureEmbeds to return a fresh mock for each test.
    This ensures isolation even if the module was previously loaded.
    """
    with patch('game_systems.adventure.ui.adventure_embeds.discord') as mock_discord:
        # Configure side_effect to return a NEW MagicMock each time Embed() is called
        mock_discord.Embed.side_effect = lambda **kwargs: MagicMock()
        yield mock_discord

def test_build_status_embed_with_stance(mock_discord_embed):
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

    # Verify Stance Field via Mock calls on the returned embed instance
    found = False
    for call in embed.add_field.call_args_list:
        if call.kwargs.get("name") == "⚔️ Tactics":
            found = True
            val = call.kwargs.get("value")
            assert "⚔️ **Aggressive**" in val
            assert "High Dmg" in val
            break

    assert found, "Tactics field not added"

def test_build_status_embed_without_monster(mock_discord_embed):
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

def test_build_status_embed_default_stance(mock_discord_embed):
    # Mock data
    session = {
        "location_id": "forest_clearing",
        "active_monster_json": json.dumps({
            "name": "Goblin",
            "HP": 50,
            "max_hp": 50
            # No player_stance key -> defaults to balanced
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
