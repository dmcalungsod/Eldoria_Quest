import importlib
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add repo root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestAdventureEmbeds(unittest.TestCase):
    def setUp(self):
        # Patch sys.modules
        self.modules_patcher = patch.dict(sys.modules)
        self.modules_patcher.start()

        # Mock Discord
        mock_discord = MagicMock()
        mock_discord.Color.dark_red.return_value = "dark_red"
        mock_discord.Color.dark_green.return_value = "dark_green"
        mock_discord.Color.dark_grey.return_value = "dark_grey"

        sys.modules["discord"] = mock_discord

        # Mock Dependencies
        sys.modules["cogs"] = MagicMock()
        mock_ui_helpers = MagicMock()
        mock_ui_helpers.make_progress_bar.return_value = "[|||||]"
        mock_ui_helpers.get_health_status_emoji.return_value = "💚"
        sys.modules["cogs.utils.ui_helpers"] = mock_ui_helpers

        # Mock Pymongo
        sys.modules["pymongo"] = MagicMock()
        sys.modules["pymongo.errors"] = MagicMock()

        # Import module under test
        import game_systems.adventure.ui.adventure_embeds

        importlib.reload(game_systems.adventure.ui.adventure_embeds)

        self.AdventureEmbeds = game_systems.adventure.ui.adventure_embeds.AdventureEmbeds

        from game_systems.player.player_stats import PlayerStats

        self.PlayerStats = PlayerStats

        self.stats = MagicMock(spec=self.PlayerStats)
        self.stats.max_hp = 100
        self.stats.max_mp = 50
        self.vitals = {"current_hp": 100, "current_mp": 50}
        self.log = ["Log entry 1", "Log entry 2"]

    def tearDown(self):
        self.modules_patcher.stop()

    def test_exploration_footer(self):
        """Test footer text when NO monster is active (Exploration Mode)."""
        embed = self.AdventureEmbeds.build_exploration_embed(
            location_id="loc_1",
            log=self.log,
            player_stats=self.stats,
            vitals=self.vitals,
            active_monster=None,  # No monster
        )

        # Verify footer text
        expected_footer = "Press Forward to continue • Field Pack to manage items"
        embed.set_footer.assert_called_with(text=expected_footer)

    def test_combat_footer(self):
        """Test footer text when a monster IS active (Combat Mode)."""
        monster = {"name": "Goblin", "hp": 50, "max_hp": 50}

        embed = self.AdventureEmbeds.build_exploration_embed(
            location_id="loc_1",
            log=self.log,
            player_stats=self.stats,
            vitals=self.vitals,
            active_monster=monster,  # Active monster
        )

        # Verify footer text changes to combat instructions
        expected_footer = "Choose your combat action • Field Pack to use items"
        embed.set_footer.assert_called_with(text=expected_footer)


if __name__ == "__main__":
    unittest.main()
