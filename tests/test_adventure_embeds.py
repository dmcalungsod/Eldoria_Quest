import sys
import unittest
from unittest.mock import MagicMock, patch
import importlib
import os

# Add path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game_systems.player.player_stats import PlayerStats

class TestAdventureEmbeds(unittest.TestCase):
    def setUp(self):
        # 1. Mock Discord and Dependencies using patch.dict
        self.mock_discord = MagicMock()
        self.mock_discord.Color.dark_red.return_value = "dark_red"
        self.mock_discord.Color.dark_green.return_value = "dark_green"
        self.mock_discord.Color.dark_grey.return_value = "dark_grey"

        self.mock_ui_helpers = MagicMock()
        self.mock_ui_helpers.make_progress_bar.return_value = "[|||||]"
        self.mock_ui_helpers.get_health_status_emoji.return_value = "💚"

        self.modules_patcher = patch.dict(sys.modules, {
            "discord": self.mock_discord,
            "cogs.ui_helpers": self.mock_ui_helpers
        })
        self.modules_patcher.start()

        # 2. Import/Reload module under test
        if "game_systems.adventure.ui.adventure_embeds" in sys.modules:
            del sys.modules["game_systems.adventure.ui.adventure_embeds"]

        import game_systems.adventure.ui.adventure_embeds
        self.AdventureEmbeds = game_systems.adventure.ui.adventure_embeds.AdventureEmbeds

        self.stats = MagicMock(spec=PlayerStats)
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
