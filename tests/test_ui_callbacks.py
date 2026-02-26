import asyncio
import os
import sys
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

# Mock pymongo globally
sys.modules["pymongo"] = MagicMock()
sys.modules["pymongo.errors"] = MagicMock()
sys.modules["pymongo.collection"] = MagicMock()
sys.modules["pymongo.results"] = MagicMock()

# Adjust path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock discord
mock_discord = MagicMock()
mock_discord.Color = MagicMock()
mock_discord.Embed = MagicMock()
# sys.modules["discord"] = mock_discord  <-- Don't do global assignment if using patch.dict
# sys.modules["discord.ui"] = MagicMock()

# Import the module under test
# We can't import it here if we want to isolate dependencies properly in setUp
# But typically we import what we want to test.
# cogs.utils.ui_helpers imports DatabaseManager etc at module level.
# We need to mock those.

# Let's import it inside tests or after setup, but we need patch.dict active.

class TestUICallbacks(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.module_patcher = patch.dict(sys.modules, {
            "discord": mock_discord,
            "discord.ui": MagicMock(),
            "game_systems.character.ui.profile_view": MagicMock(),
            "game_systems.guild_system.ui.lobby_view": MagicMock()
        })
        self.module_patcher.start()

        # Now import/reload the module
        import cogs.utils.ui_helpers
        import importlib
        importlib.reload(cogs.utils.ui_helpers)
        self.ui_helpers = cogs.utils.ui_helpers

        self.mock_interaction = MagicMock()
        self.mock_interaction.user.id = 12345
        self.mock_interaction.response = MagicMock()
        self.mock_interaction.response.is_done.return_value = False
        self.mock_interaction.response.send_message = AsyncMock()
        self.mock_interaction.response.defer = AsyncMock()
        self.mock_interaction.followup = MagicMock()
        self.mock_interaction.followup.send = AsyncMock()
        self.mock_interaction.edit_original_response = AsyncMock()

    def tearDown(self):
        self.module_patcher.stop()

    @patch("cogs.utils.ui_helpers.DatabaseManager")
    async def test_get_player_or_error_found(self, MockDB):
        """Test getting player successfully."""
        mock_db_instance = MockDB.return_value
        mock_db_instance.get_player.return_value = {"name": "Hero"}

        player = await self.ui_helpers.get_player_or_error(self.mock_interaction, mock_db_instance)

        self.assertEqual(player["name"], "Hero")
        self.mock_interaction.response.send_message.assert_not_called()

    @patch("cogs.utils.ui_helpers.DatabaseManager")
    async def test_get_player_or_error_not_found(self, MockDB):
        """Test player not found."""
        mock_db_instance = MockDB.return_value
        mock_db_instance.get_player.return_value = None

        player = await self.ui_helpers.get_player_or_error(self.mock_interaction, mock_db_instance)

        self.assertIsNone(player)
        self.mock_interaction.response.send_message.assert_called_with("Character record not found.", ephemeral=True)

    @patch("cogs.utils.ui_helpers.DatabaseManager")
    async def test_back_to_profile_callback_success(self, MockDB):
        # Configure the mock module we injected
        mock_profile_view_mod = sys.modules["game_systems.character.ui.profile_view"]
        mock_profile_view_mod.CharacterTabView = MagicMock()

        mock_db_instance = MockDB.return_value

        # Setup profile bundle
        bundle = {
            "player": {"name": "Hero", "class_id": 1, "level": 5, "current_hp": 100, "current_mp": 50, "experience": 100, "exp_to_next": 1000},
            "stats": {"strength": 10, "endurance": 10, "dexterity": 10, "agility": 10, "magic": 10, "luck": 10, "max_hp": 100, "max_mp": 50, "max_inventory_slots": 20, "INVENTORY_STR_MOD": 0.5, "INVENTORY_DEX_MOD": 0.25},
            "guild": {"rank": "F"}
        }
        mock_db_instance.get_profile_bundle.return_value = bundle
        mock_db_instance.get_class.return_value = {"name": "Warrior"}
        mock_db_instance.get_inventory_slot_count.return_value = 5

        await self.ui_helpers.back_to_profile_callback(self.mock_interaction)

        # Verify interaction edit
        self.mock_interaction.edit_original_response.assert_called()
        args, kwargs = self.mock_interaction.edit_original_response.call_args
        self.assertIn('embed', kwargs)
        # Verify view creation
        mock_profile_view_mod.CharacterTabView.assert_called()

    @patch("cogs.utils.ui_helpers.DatabaseManager")
    async def test_back_to_guild_hall_callback_success(self, MockDB):
        mock_lobby_view_mod = sys.modules["game_systems.guild_system.ui.lobby_view"]
        mock_lobby_view_mod.GuildLobbyView = MagicMock()

        mock_db_instance = MockDB.return_value
        mock_db_instance.get_player.return_value = {"name": "Hero"}
        mock_db_instance.get_guild_card_data.return_value = {"name": "Hero", "rank": "F"}

        await self.ui_helpers.back_to_guild_hall_callback(self.mock_interaction)

        self.mock_interaction.edit_original_response.assert_called()
        mock_lobby_view_mod.GuildLobbyView.assert_called()


if __name__ == "__main__":
    unittest.main()
