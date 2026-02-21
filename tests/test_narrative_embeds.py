import sys
import unittest
from unittest.mock import MagicMock, patch
import os

# Add repo root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestNarrativeEmbeds(unittest.TestCase):
    def setUp(self):
        # Patch sys.modules to mock dependencies
        self.modules_patcher = patch.dict(sys.modules)
        self.modules_patcher.start()

        # Mock discord
        self.mock_discord = MagicMock()
        self.mock_discord.Color.gold.return_value = "gold"
        self.mock_discord.Color.dark_green.return_value = "dark_green"
        self.mock_discord.Color.dark_red.return_value = "dark_red"

        # Setup Embed mock to capture attributes
        def embed_side_effect(*args, **kwargs):
            mock_obj = MagicMock()
            mock_obj.title = kwargs.get('title')
            mock_obj.description = kwargs.get('description')
            mock_obj.color = kwargs.get('color')
            mock_obj.fields = []
            def add_field(name, value, inline=True):
                mock_obj.fields.append({'name': name, 'value': value, 'inline': inline})
            mock_obj.add_field.side_effect = add_field
            mock_obj.set_footer = MagicMock()
            return mock_obj

        self.mock_discord.Embed.side_effect = embed_side_effect
        sys.modules["discord"] = self.mock_discord

        # Mock other dependencies
        sys.modules["cogs"] = MagicMock()
        sys.modules["cogs.ui_helpers"] = MagicMock()
        sys.modules["game_systems.player.player_stats"] = MagicMock()
        sys.modules["game_systems.world_time"] = MagicMock()

        # Ensure we can import the module under test
        # We need to make sure 'game_systems' package is importable
        # Since we added repo root to path, it should be fine.

        # We also need to ensure narrative_data is importable.
        import game_systems.adventure.ui.adventure_embeds
        import game_systems.data.narrative_data

        # Reload to ensure mocks are applied if already imported
        import importlib
        importlib.reload(game_systems.adventure.ui.adventure_embeds)

        self.AdventureEmbeds = game_systems.adventure.ui.adventure_embeds.AdventureEmbeds
        self.MISSION_FLAVOR_TEXT = game_systems.data.narrative_data.MISSION_FLAVOR_TEXT
        self.OUTCOME_FLAVOR_TEXT = game_systems.data.narrative_data.OUTCOME_FLAVOR_TEXT

    def tearDown(self):
        self.modules_patcher.stop()

    def test_build_summary_embed_level_up(self):
        summary = {"leveled_up": True, "old_level": 1, "new_level": 2}
        location_id = "forest_outskirts"

        embed = self.AdventureEmbeds.build_summary_embed(summary, location_id)

        # Check title
        self.assertIn("Level Up", str(embed.title))
        self.assertEqual(embed.color, "gold")

        # Check description comes from OUTCOME_FLAVOR_TEXT["level_up"]
        description = embed.description.replace("*", "") # Remove italics
        self.assertIn(description, self.OUTCOME_FLAVOR_TEXT["level_up"])

    def test_build_summary_embed_location_flavor(self):
        summary = {"leveled_up": False}
        location_id = "forest_outskirts"

        embed = self.AdventureEmbeds.build_summary_embed(summary, location_id)

        # Check title
        self.assertIn("Expedition Complete", str(embed.title))
        self.assertEqual(embed.color, "dark_green")

        # Check description comes from MISSION_FLAVOR_TEXT["forest_outskirts"]
        description = embed.description.replace("*", "")
        self.assertIn(description, self.MISSION_FLAVOR_TEXT["forest_outskirts"])

    def test_build_summary_embed_unknown_location(self):
        summary = {"leveled_up": False}
        location_id = "unknown_place"

        embed = self.AdventureEmbeds.build_summary_embed(summary, location_id)

        # Check description comes from OUTCOME_FLAVOR_TEXT["default"]
        description = embed.description.replace("*", "")
        self.assertIn(description, self.OUTCOME_FLAVOR_TEXT["default"])

if __name__ == "__main__":
    unittest.main()
