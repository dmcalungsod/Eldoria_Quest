import sys
import unittest
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio

# Mock pymongo globally
sys.modules["pymongo"] = MagicMock()
sys.modules["pymongo.errors"] = MagicMock()
sys.modules["pymongo.collection"] = MagicMock()
sys.modules["pymongo.results"] = MagicMock()

import discord
import discord.ui

# Mock the discord UI elements appropriately without completely redefining packages
class MockView(discord.ui.View):
    def __init__(self, timeout=None):
        super().__init__(timeout=timeout)
        self.children = []
        self.items = []

    def add_item(self, item):
        self.children.append(item)
        self.items.append(item)

# Now import the module to test
from game_systems.character.ui.adventure_menu import AdventureView
from game_systems.adventure.ui.adventure_embeds import AdventureEmbeds

class TestAdventureMenu(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.mock_db = MagicMock()
        self.mock_user = MagicMock()
        self.mock_user.id = 12345

        self.mock_interaction = AsyncMock()
        self.mock_interaction.user = self.mock_user
        # Must be a regular MagicMock since it returns a bool synchronously
        self.mock_interaction.response.is_done = MagicMock(return_value=False)
        self.mock_interaction.client = MagicMock()

        self.mock_adventure_cog = MagicMock()
        self.mock_interaction.client.get_cog.return_value = self.mock_adventure_cog

    @patch("discord.ui.View", MockView)
    def test_init_resume(self):
        """Test the initialization for resuming."""
        view = AdventureView(self.mock_db, self.mock_user, active_session=True)
        # Using children because actual View uses children
        self.assertEqual(len(view.children), 2)
        start_btn = view.children[0]
        self.assertEqual(start_btn.label, "Resume Expedition")
        self.assertEqual(start_btn.emoji.name, "🧭")

    @patch("discord.ui.View", MockView)
    def test_init_begin(self):
        """Test the initialization for beginning."""
        view = AdventureView(self.mock_db, self.mock_user, active_session=False)
        self.assertEqual(len(view.children), 2)
        start_btn = view.children[0]
        self.assertEqual(start_btn.label, "Begin Expedition")
        self.assertEqual(start_btn.emoji.name, "⚔️")

    @patch("discord.ui.View", MockView)
    async def test_interaction_check_success(self):
        view = AdventureView(self.mock_db, self.mock_user)
        result = await view.interaction_check(self.mock_interaction)
        self.assertTrue(result)
        self.mock_interaction.response.send_message.assert_not_called()

    @patch("discord.ui.View", MockView)
    async def test_interaction_check_fail(self):
        view = AdventureView(self.mock_db, self.mock_user)
        wrong_user_interaction = AsyncMock()
        wrong_user_interaction.user.id = 99999
        result = await view.interaction_check(wrong_user_interaction)
        self.assertFalse(result)
        wrong_user_interaction.response.send_message.assert_called_once_with("This is not your session.", ephemeral=True)

    @patch("discord.ui.View", MockView)
    async def test_start_adventure_callback_no_cog(self):
        self.mock_interaction.client.get_cog.return_value = None
        view = AdventureView(self.mock_db, self.mock_user)

        await view.start_adventure_callback(self.mock_interaction)

        self.mock_interaction.response.send_message.assert_called_once()
        args, kwargs = self.mock_interaction.response.send_message.call_args
        self.assertIn("The adventure system is currently unavailable.", args[0])

    @patch("game_systems.character.ui.adventure_menu.AdventureEmbeds")
    @patch("discord.ui.View", MockView)
    async def test_start_adventure_callback_resume_completed(self, MockEmbeds):
        session = {"status": "completed", "location_id": "forest"}
        self.mock_adventure_cog.manager.get_active_session.return_value = session

        summary = {"xp": 100, "materials": {}}
        self.mock_adventure_cog.manager.end_adventure.return_value = summary

        MockEmbeds.build_summary_embed.return_value = MagicMock()

        view = AdventureView(self.mock_db, self.mock_user)
        await view.start_adventure_callback(self.mock_interaction)

        self.mock_interaction.response.defer.assert_called_once()
        self.mock_adventure_cog.manager.end_adventure.assert_called_once_with(12345)
        MockEmbeds.build_summary_embed.assert_called_once_with(summary, "forest")
        self.mock_interaction.edit_original_response.assert_called_once()

    @patch("game_systems.character.ui.adventure_menu.AdventureStatusView")
    @patch("game_systems.character.ui.adventure_menu.AdventureEmbeds")
    @patch("discord.ui.View", MockView)
    async def test_start_adventure_callback_resume_in_progress(self, MockEmbeds, MockStatusView):
        session = {"status": "in_progress", "location_id": "forest"}
        self.mock_adventure_cog.manager.get_active_session.return_value = session

        MockEmbeds.build_adventure_status_embed.return_value = MagicMock()
        MockStatusView.return_value = MagicMock()

        view = AdventureView(self.mock_db, self.mock_user)
        await view.start_adventure_callback(self.mock_interaction)

        self.mock_interaction.response.defer.assert_called_once()
        MockEmbeds.build_adventure_status_embed.assert_called_once_with(session)
        MockStatusView.assert_called_once_with(self.mock_db, self.mock_adventure_cog.manager, self.mock_user, session)
        self.mock_interaction.edit_original_response.assert_called_once()

    @patch("game_systems.character.ui.adventure_menu.AdventureSetupView")
    @patch("discord.ui.View", MockView)
    async def test_start_adventure_callback_new_adventure(self, MockSetupView):
        self.mock_adventure_cog.manager.get_active_session.return_value = None

        self.mock_db.get_guild_member_data.return_value = {"rank": "C"}
        self.mock_db.get_player.return_value = {"level": 10}
        self.mock_db.get_inventory_items.return_value = [{"item_key": "potion", "item_type": "hp"}]
        self.mock_db.calculate_inventory_limit.return_value = 20
        self.mock_db.get_inventory_slot_count.return_value = 5

        MockSetupView.return_value = MagicMock()

        view = AdventureView(self.mock_db, self.mock_user)
        await view.start_adventure_callback(self.mock_interaction)

        self.mock_interaction.response.defer.assert_called_once()
        self.mock_db.get_guild_member_data.assert_called_once_with(12345)
        self.mock_db.get_player.assert_called_once_with(12345)

        MockSetupView.assert_called_once()
        self.mock_interaction.edit_original_response.assert_called_once()
        args, kwargs = self.mock_interaction.edit_original_response.call_args
        self.assertIn("embed", kwargs)
        self.assertIn("view", kwargs)

if __name__ == "__main__":
    unittest.main()
