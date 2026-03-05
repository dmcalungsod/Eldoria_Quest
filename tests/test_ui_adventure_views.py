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


# --- Mocking Discord UI ---
class MockItem:
    def __init__(self, *args, **kwargs):
        self.label = kwargs.get("label")
        self.custom_id = kwargs.get("custom_id")
        self.disabled = kwargs.get("disabled", False)
        self.options = kwargs.get("options", [])
        self.callback = None
        self.values = []  # For Select

    def add_option(self, label, value, **kwargs):
        self.options.append(MagicMock(label=label, value=str(value)))


class MockButton(MockItem):
    pass


class MockSelect(MockItem):
    pass


class MockView:
    def __init__(self, timeout=180):
        self.children = []
        self.timeout = timeout

    def add_item(self, item):
        self.children.append(item)

    def clear_items(self):
        self.children = []


# Mock discord module
class MockEmbed:
    def __init__(self, **kwargs):
        self.title = kwargs.get("title")
        self.description = kwargs.get("description")
        self.color = kwargs.get("color")
        self.fields = []

    def add_field(self, name, value, inline=False):
        field = MagicMock()
        field.name = name
        field.value = value
        field.inline = inline
        self.fields.append(field)

mock_discord = MagicMock()
mock_discord.ButtonStyle = MagicMock()
mock_discord.Color = MagicMock()
mock_discord.Embed = MockEmbed
mock_discord.ui.View = MockView
mock_discord.ui.Button = MockButton
mock_discord.ui.Select = MockSelect
sys.modules["discord"] = mock_discord
sys.modules["discord.ui"] = mock_discord.ui
sys.modules["discord.ext"] = MagicMock()
sys.modules["discord.ext.commands"] = MagicMock()

from game_systems.adventure.ui.status_view import AdventureStatusView


class TestAdventureStatusView(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.mock_db = MagicMock()
        self.mock_manager = MagicMock()
        self.mock_user = MagicMock()
        self.mock_user.id = 12345
        self.session_data = {"location_id": "forest"}
        self.mock_interaction = AsyncMock()
        self.mock_interaction.user = self.mock_user
        self.mock_interaction.response = AsyncMock()
        self.mock_interaction.response.is_done.return_value = False

    def test_init(self):
        """Test initialization."""
        view = AdventureStatusView(self.mock_db, self.mock_manager, self.mock_user, self.session_data)

        self.assertEqual(len(view.children), 3)  # Refresh, Retreat, Back
        labels = [c.label for c in view.children]
        self.assertIn("Refresh Status", labels)
        self.assertIn("Retreat Early", labels)
        self.assertIn("Return to Profile", labels)

    async def test_interaction_check(self):
        """Test interaction check."""
        view = AdventureStatusView(self.mock_db, self.mock_manager, self.mock_user, self.session_data)

        # Valid user
        result = await view.interaction_check(self.mock_interaction)
        self.assertTrue(result)

        # Invalid user
        other_user = MagicMock()
        other_user.id = 999
        self.mock_interaction.user = other_user
        result = await view.interaction_check(self.mock_interaction)
        self.assertFalse(result)

    @patch("game_systems.adventure.ui.status_view.AdventureEmbeds")
    async def test_refresh_callback_success(self, MockEmbeds):
        """Test successful refresh."""
        self.mock_manager.get_active_session.return_value = self.session_data
        MockEmbeds.build_adventure_status_embed.return_value = MagicMock()

        view = AdventureStatusView(self.mock_db, self.mock_manager, self.mock_user, self.session_data)

        await view.refresh_callback(self.mock_interaction)

        self.mock_manager.get_active_session.assert_called_with(12345)
        self.mock_interaction.edit_original_response.assert_called()

    async def test_refresh_callback_session_ended(self):
        """Test refresh when session is ended."""
        self.mock_manager.get_active_session.return_value = None

        view = AdventureStatusView(self.mock_db, self.mock_manager, self.mock_user, self.session_data)

        await view.refresh_callback(self.mock_interaction)

        # Should verify buttons are disabled (except back)
        # Assuming refresh_btn is index 0, retreat_btn is index 1, back_btn is index 2
        self.assertTrue(view.children[0].disabled)
        self.assertTrue(view.children[1].disabled)
        self.assertFalse(view.children[2].disabled)

        self.mock_interaction.followup.send.assert_called_with(
            "Adventure session not found or already ended.", ephemeral=True
        )

    @patch("game_systems.adventure.ui.status_view.AdventureEmbeds")
    async def test_retreat_callback_success(self, MockEmbeds):
        """Test successful retreat."""
        summary = {"xp": 100}
        self.mock_manager.end_adventure.return_value = summary
        MockEmbeds.build_summary_embed.return_value = MagicMock()

        view = AdventureStatusView(self.mock_db, self.mock_manager, self.mock_user, self.session_data)

        await view.retreat_callback(self.mock_interaction)

        self.mock_manager.end_adventure.assert_called_with(12345)

        # View items should be cleared and replaced with Back button
        # clear_items calls children = []
        # then add_item adds Back button
        self.assertEqual(len(view.children), 1)
        self.assertEqual(view.children[0].label, "Return to Profile")

        self.mock_interaction.edit_original_response.assert_called()

class TestAdventureSetupView(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.mock_db = MagicMock()
        self.mock_manager = MagicMock()
        self.mock_user = MagicMock()
        self.mock_user.id = 12345

        self.mock_interaction = AsyncMock()
        self.mock_interaction.user = self.mock_user
        self.mock_interaction.response = AsyncMock()
        self.mock_interaction.followup = AsyncMock()

    @patch("cogs.utils.ui_helpers.get_player_or_error")
    async def test_start_callback_low_hp(self, mock_get_player_or_error):
        """Test start_callback when player has critically low HP."""
        # Setup mocks
        mock_get_player_or_error.return_value = {"id": 12345}

        # Mock vitals returning < 15% HP
        self.mock_db.get_player_vitals.return_value = {"current_hp": 8}

        from game_systems.player.player_stats import PlayerStats
        stats = PlayerStats()
        stats.base_health = 100
        self.mock_db.get_player_stats_json.return_value = stats.to_dict()

        from game_systems.adventure.ui.setup_view import AdventureSetupView
        view = AdventureSetupView(
            db=self.mock_db,
            manager=self.mock_manager,
            interaction_user=self.mock_user,
            player_rank="F",
            player_level=1
        )
        # Mock view state needed for callback
        view.selected_location = "forest"
        view.selected_duration = 30
        view.selected_supplies = []

        await view.start_callback(self.mock_interaction)

        # Ensure we sent the ephemeral warning
        self.mock_interaction.response.send_message.assert_called_once()
        args, kwargs = self.mock_interaction.response.send_message.call_args
        self.assertIn("health is critically low", args[0])
        self.assertTrue(kwargs.get("ephemeral"))

        # Ensure we didn't start the adventure
        self.mock_manager.start_adventure.assert_not_called()

    @patch("game_systems.adventure.ui.adventure_embeds.AdventureEmbeds.build_adventure_status_embed")
    @patch("cogs.utils.ui_helpers.get_player_or_error")
    async def test_start_callback_success(self, mock_get_player_or_error, mock_build_adventure_status_embed):
        """Test start_callback handles a normal flow successfully."""
        # Setup mocks
        mock_get_player_or_error.return_value = {"id": 12345}

        # Mock vitals returning >= 15% HP
        self.mock_db.get_player_vitals.return_value = {"current_hp": 100}

        from game_systems.player.player_stats import PlayerStats
        stats = PlayerStats()
        stats.base_health = 100
        self.mock_db.get_player_stats_json.return_value = stats.to_dict()

        # Mock manager start success
        self.mock_manager.start_adventure.return_value = True
        self.mock_manager.get_active_session.return_value = {
            "location_id": "forest",
        }

        mock_build_adventure_status_embed.return_value = MagicMock()

        from game_systems.adventure.ui.setup_view import AdventureSetupView
        view = AdventureSetupView(
            db=self.mock_db,
            manager=self.mock_manager,
            interaction_user=self.mock_user,
            player_rank="F",
            player_level=1
        )
        # Mock view state needed for callback
        view.selected_location = "forest"
        view.selected_duration = 30
        view.selected_supplies = ["none"]

        await view.start_callback(self.mock_interaction)

        # Ensure we deferred the response
        self.mock_interaction.response.defer.assert_called_once()

        # Ensure we started the adventure
        self.mock_manager.start_adventure.assert_called_once_with(
            12345, "forest", 30, supplies={}
        )

        # Ensure we edited the original response with the new view
        self.mock_interaction.edit_original_response.assert_called_once()


if __name__ == "__main__":
    unittest.main()

class TestAdventureMenuView(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.mock_db = MagicMock()
        self.mock_manager = MagicMock()
        self.mock_user = MagicMock()
        self.mock_user.id = 12345
        self.mock_interaction = AsyncMock()
        self.mock_interaction.user = self.mock_user
        self.mock_interaction.client = MagicMock()
        self.mock_interaction.response = AsyncMock()
        self.mock_interaction.edit_original_response = AsyncMock()
        self.mock_interaction.followup = AsyncMock()

        # Mock cog manager
        mock_cog = MagicMock()
        mock_cog.manager = self.mock_manager
        self.mock_interaction.client.get_cog.return_value = mock_cog

    @patch("game_systems.character.ui.adventure_menu.AdventureSetupView")
    async def test_start_adventure_callback_new_player(self, MockSetupView):
        """Test start_adventure_callback for a new player with 0 expeditions."""
        from game_systems.character.ui.adventure_menu import AdventureView

        # Setup mocks for parallel DB fetch
        self.mock_db.get_guild_member_data.return_value = {"rank": "F"}
        self.mock_db.get_player.return_value = {"level": 1}
        self.mock_db.get_inventory_items.return_value = []
        self.mock_db.calculate_inventory_limit.return_value = 20
        self.mock_db.get_inventory_slot_count.return_value = 5

        # This is the key mock: return 0 expeditions
        self.mock_db.get_exploration_stats.return_value = {
            "unique_locations": [],
            "total_expeditions": 0
        }

        # Ensure no active session
        self.mock_manager.get_active_session.return_value = None

        view = AdventureView(self.mock_db, self.mock_user, active_session=False)

        await view.start_adventure_callback(self.mock_interaction)

        # Ensure interaction was deferred
        self.mock_interaction.response.defer.assert_called_once()

        # Ensure edit_original_response was called with an embed and view
        self.mock_interaction.edit_original_response.assert_called_once()
        args, kwargs = self.mock_interaction.edit_original_response.call_args

        embed = kwargs.get("embed")
        self.assertIsNotNone(embed)

        # In a test suite where discord is heavily mocked globally,
        # embed.add_field might be a MagicMock instead of our custom class method.
        # Check if add_field was called.
        if hasattr(embed.add_field, 'call_args_list') and embed.add_field.call_args_list:
            # It's a MagicMock, let's verify the calls
            mentor_call = None
            for call in embed.add_field.call_args_list:
                _, call_kwargs = call
                if "Mentor's Advice" in call_kwargs.get("name", ""):
                    mentor_call = call_kwargs
                    break
            self.assertIsNotNone(mentor_call, "Mentor's Advice field was not added.")
            self.assertIn("The Whispering Forest", mentor_call.get("value", ""))
            self.assertIn("30 Minutes", mentor_call.get("value", ""))
        else:
            # It might be our custom MockEmbed
            fields = getattr(embed, "fields", [])
            mentor_field = next((f for f in fields if getattr(f, "name", "") and "Mentor's Advice" in f.name), None)
            self.assertIsNotNone(mentor_field, "Mentor's Advice field was not found in the embed for new player.")
            self.assertIn("The Whispering Forest", mentor_field.value)
            self.assertIn("30 Minutes", mentor_field.value)
