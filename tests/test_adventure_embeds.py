import sys
import unittest
from unittest.mock import MagicMock

# 1. Mock Discord and Dependencies
mock_discord = MagicMock()
mock_discord.Color.dark_red.return_value = "dark_red"
mock_discord.Color.dark_green.return_value = "dark_green"
mock_discord.Color.dark_grey.return_value = "dark_grey"

# Forcefully remove discord to ensure mocks take precedence
if "discord" in sys.modules:
    del sys.modules["discord"]

sys.modules["discord"] = mock_discord
sys.modules["cogs"] = MagicMock()
sys.modules["cogs.ui_helpers"] = MagicMock()

# Mock make_progress_bar
sys.modules["cogs.ui_helpers"].make_progress_bar = MagicMock(return_value="[|||||]")
sys.modules["cogs.ui_helpers"].get_health_status_emoji = MagicMock(return_value="💚")

# 2. Add path and Import
import importlib  # noqa: E402
import os  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Ensure we are using the REAL module, not a mock from another test
if "game_systems.adventure.ui.adventure_embeds" in sys.modules:
    del sys.modules["game_systems.adventure.ui.adventure_embeds"]

import game_systems.adventure.ui.adventure_embeds  # noqa: E402

importlib.reload(game_systems.adventure.ui.adventure_embeds)
from game_systems.adventure.ui.adventure_embeds import AdventureEmbeds  # noqa: E402
from game_systems.player.player_stats import PlayerStats  # noqa: E402


class TestAdventureEmbeds(unittest.TestCase):
    def setUp(self):
        self.stats = MagicMock(spec=PlayerStats)
        self.stats.max_hp = 100
        self.stats.max_mp = 50
        self.vitals = {"current_hp": 100, "current_mp": 50}
        self.log = ["Log entry 1", "Log entry 2"]

    def test_exploration_footer(self):
        """Test footer text when NO monster is active (Exploration Mode)."""
        embed = AdventureEmbeds.build_exploration_embed(
            location_id="loc_1",
            log=self.log,
            player_stats=self.stats,
            vitals=self.vitals,
            active_monster=None  # No monster
        )

        # Verify footer text
        expected_footer = "Press Forward to continue • Field Pack to manage items"
        embed.set_footer.assert_called_with(text=expected_footer)

    def test_combat_footer(self):
        """Test footer text when a monster IS active (Combat Mode)."""
        monster = {"name": "Goblin", "hp": 50, "max_hp": 50}

        embed = AdventureEmbeds.build_exploration_embed(
            location_id="loc_1",
            log=self.log,
            player_stats=self.stats,
            vitals=self.vitals,
            active_monster=monster  # Active monster
        )

        # Verify footer text changes to combat instructions
        expected_footer = "Choose your combat action • Field Pack to use items"
        embed.set_footer.assert_called_with(text=expected_footer)

if __name__ == "__main__":
    unittest.main()
