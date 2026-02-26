import importlib
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Configure sys.modules with mocks FIRST
mock_pymongo = MagicMock()
mock_pymongo.errors = MagicMock()
sys.modules["pymongo"] = mock_pymongo
sys.modules["pymongo.errors"] = mock_pymongo.errors

mock_discord = MagicMock()
mock_discord.ButtonStyle.primary = "primary"
mock_discord.ButtonStyle.secondary = "secondary"
mock_discord.ButtonStyle.grey = "grey"
mock_discord.Color.dark_grey.return_value = "dark_grey"
mock_discord.Color.green.return_value = "green"
mock_discord.Color.red.return_value = "red"

mock_ui = MagicMock()


class MockEmbed:
    def __init__(self, title=None, description=None, color=None, **kwargs):
        self.title = title or ""
        self.description = description or ""
        self.color = color
        self.fields = []

    def set_footer(self, text=None):
        pass

    def add_field(self, name, value, inline=False):
        self.fields.append({"name": name, "value": value})
        # Retrieve the CURRENT global discord mock and apply MockEmbed
        import cogs.infirmary_cog as infirmary_cog

        infirmary_cog.discord.Embed.side_effect = MockEmbed



class MockView:
    def __init__(self, timeout=None):
        self.children = []

    def add_item(self, item):
        self.children.append(item)


mock_ui.View = MockView


class MockButton:
    def __init__(self, label=None, style=None, custom_id=None, row=None, emoji=None, disabled=False):
        self.label = label
        self.style = style
        self.custom_id = custom_id
        self.row = row
        self.emoji = emoji
        self.disabled = disabled
        self.callback = None


mock_ui.Button = MockButton

sys.modules["discord"] = mock_discord
sys.modules["discord.ui"] = mock_ui
sys.modules["discord.ext"] = MagicMock()
sys.modules["discord.ext.commands"] = MagicMock()

# Add repo root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cogs.infirmary_cog  # noqa: E402

importlib.reload(cogs.infirmary_cog)
from cogs.infirmary_cog import InfirmaryView  # noqa: E402
from game_systems.player.player_stats import PlayerStats  # noqa: E402


class TestInfirmaryView(unittest.TestCase):
    def setUp(self):
        self.mock_db = MagicMock()
        self.mock_user = MagicMock()
        self.mock_user.id = 12345

        import cogs.infirmary_cog
        cogs.infirmary_cog.discord.Embed.side_effect = MockEmbed
        if not hasattr(cogs.infirmary_cog.discord.ButtonStyle, "secondary"):
            cogs.infirmary_cog.discord.ButtonStyle.secondary = "secondary"
        else:
            cogs.infirmary_cog.discord.ButtonStyle.secondary = "secondary"
        cogs.infirmary_cog.discord.ButtonStyle.success = "success"
        cogs.infirmary_cog.discord.Color.green.return_value = "green"
        cogs.infirmary_cog.discord.Color.red.return_value = "red"


        self.stats = MagicMock(spec=PlayerStats)
        self.stats.max_hp = 100
        self.stats.max_mp = 50

    def test_init_fully_restored(self):
        """Test the View when player is already at full HP/MP."""
        p_data = {"current_hp": 100, "current_mp": 50, "aurum": 500}

        # We need to mock calculating cost returning 0
        with patch("cogs.infirmary_cog.DatabaseManager.calculate_heal_cost", return_value=0):
            view = InfirmaryView(self.mock_db, self.mock_user, p_data, self.stats)

            # Heal button should be disabled
            heal_btn = next((b for b in view.children if b.custom_id == "heal_btn"), None)
            self.assertIsNotNone(heal_btn)
            self.assertTrue(heal_btn.disabled)
            self.assertEqual(heal_btn.label, "Fully Restored")
            self.assertEqual(heal_btn.style, "secondary")

    def test_init_insufficient_funds(self):
        """Test the View when player is hurt but has no money."""
        p_data = {"current_hp": 10, "current_mp": 50, "aurum": 5}

        # Missing 90 HP means cost is 180
        with patch("cogs.infirmary_cog.DatabaseManager.calculate_heal_cost", return_value=180):
            view = InfirmaryView(self.mock_db, self.mock_user, p_data, self.stats)

            # Heal button should be disabled
            heal_btn = next((b for b in view.children if b.custom_id == "heal_btn"), None)
            self.assertIsNotNone(heal_btn)
            self.assertTrue(heal_btn.disabled)
            self.assertEqual(heal_btn.label, "Insufficient Funds")

    def test_init_can_heal(self):
        """Test the View when player is hurt and has enough money."""
        p_data = {"current_hp": 50, "current_mp": 25, "aurum": 500}

        # Assume cost is 100
        with patch("cogs.infirmary_cog.DatabaseManager.calculate_heal_cost", return_value=100):
            view = InfirmaryView(self.mock_db, self.mock_user, p_data, self.stats)

            # Heal button should be enabled
            heal_btn = next((b for b in view.children if b.custom_id == "heal_btn"), None)
            self.assertIsNotNone(heal_btn)
            self.assertFalse(heal_btn.disabled)
            self.assertEqual(heal_btn.label, "Heal (100 G)")
            self.assertEqual(heal_btn.style, "primary")

    def test_build_embed_low_hp(self):
        """Test embed visually correctly indicates severe wound (HP < 30%)."""
        p_data = {"current_hp": 10, "current_mp": 50, "aurum": 500}  # 10% HP

        with patch("cogs.infirmary_cog.DatabaseManager.calculate_heal_cost", return_value=180):
            embed = InfirmaryView.build_infirmary_embed(p_data, self.stats)

            self.assertIn("The healers rush to your side", embed.description)
            self.assertIn("180", embed.description)

    def test_build_embed_mid_hp(self):
        """Test embed visually correctly indicates moderate wound (HP < 70%)."""
        p_data = {"current_hp": 50, "current_mp": 50, "aurum": 500}  # 50% HP

        with patch("cogs.infirmary_cog.DatabaseManager.calculate_heal_cost", return_value=100):
            embed = InfirmaryView.build_infirmary_embed(p_data, self.stats)

            self.assertIn("You limp to a cot", embed.description)

    def test_build_embed_full_hp(self):
        """Test embed visually correctly indicates full health."""
        p_data = {"current_hp": 100, "current_mp": 50, "aurum": 500}  # 100% HP

        with patch("cogs.infirmary_cog.DatabaseManager.calculate_heal_cost", return_value=0):
            embed = InfirmaryView.build_infirmary_embed(p_data, self.stats)

            self.assertIn("lanternlight fills the chamber", embed.description)
            self.assertIn("peak condition", embed.description)

    def test_build_embed_with_messages(self):
        """Test embed with success and error messages added."""
        p_data = {"current_hp": 100, "current_mp": 50, "aurum": 500}

        with patch("cogs.infirmary_cog.DatabaseManager.calculate_heal_cost", return_value=0):
            # Success
            embed_success = InfirmaryView.build_infirmary_embed(p_data, self.stats, msg="Healed fully!", success=True)
            self.assertEqual(embed_success.color, mock_discord.Color.green())
            self.assertTrue(
                any(
                    f["name"] == "Treatment Complete" and "Healed fully!" in f["value"]
                    for f in getattr(embed_success, "fields", [])
                )
            )

            # Error
            embed_error = InfirmaryView.build_infirmary_embed(
                p_data, self.stats, msg="Not enough Aurum.", success=False
            )
            self.assertEqual(embed_error.color, mock_discord.Color.red())
            self.assertTrue(
                any(
                    f["name"] == "Treatment Declined" and "Not enough Aurum." in f["value"]
                    for f in getattr(embed_error, "fields", [])
                )
            )


if __name__ == "__main__":
    unittest.main()
