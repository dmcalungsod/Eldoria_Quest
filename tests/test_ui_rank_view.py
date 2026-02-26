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

# --- Mocking Discord UI ---
class MockItem:
    def __init__(self, *args, **kwargs):
        self.label = kwargs.get("label")
        self.custom_id = kwargs.get("custom_id")
        self.disabled = kwargs.get("disabled", False)
        self.options = kwargs.get("options", [])
        self.callback = None
        self.values = []

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

    def set_back_button(self, callback, label):
        pass

# Helper to import module with mocked dependencies
def import_module_with_mocks():
    # Define mocks
    mock_discord = MagicMock()
    mock_discord.ButtonStyle = MagicMock()
    mock_discord.Color = MagicMock()
    mock_discord.ui.View = MockView
    mock_discord.ui.Button = MockButton
    mock_discord.ui.Select = MockSelect

    mock_components = MagicMock()
    class MockGuildViewMixin:
        pass
    mock_components.GuildViewMixin = MockGuildViewMixin

    # Create a dict of modules to patch
    modules = {
        "discord": mock_discord,
        "discord.ui": mock_discord.ui,
        "discord.ext": MagicMock(),
        "discord.ext.commands": MagicMock(),
        "game_systems.guild_system.ui.components": mock_components,
    }

    with patch.dict(sys.modules, modules):
        # We need to reload the module if it was already imported to apply patches
        if "game_systems.guild_system.ui.rank_view" in sys.modules:
            import importlib
            importlib.reload(sys.modules["game_systems.guild_system.ui.rank_view"])
        else:
            import game_systems.guild_system.ui.rank_view

        return sys.modules["game_systems.guild_system.ui.rank_view"]


class TestRankView(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        # Patch sys.modules for the duration of the test method
        self.module_patcher = patch.dict(sys.modules, {
            "discord": MagicMock(),
            "discord.ui": MagicMock(),
            "game_systems.guild_system.ui.components": MagicMock()
        })
        self.module_patcher.start()

        # Re-apply our specific mocks
        mock_discord = MagicMock()
        mock_discord.ButtonStyle = MagicMock()
        mock_discord.Color = MagicMock()
        mock_discord.ui.View = MockView
        mock_discord.ui.Button = MockButton
        mock_discord.ui.Select = MockSelect
        sys.modules["discord"] = mock_discord
        sys.modules["discord.ui"] = mock_discord.ui

        mock_components = MagicMock()
        class MockGuildViewMixin:
            pass
        mock_components.GuildViewMixin = MockGuildViewMixin
        # We also need to mock SystemCache and ViewFactory on mock_components
        self.mock_rank_system = MagicMock()
        mock_components.SystemCache.get_rank_system.return_value = self.mock_rank_system
        def create_button(**kwargs):
            return MockButton(**kwargs)
        mock_components.ViewFactory.create_button.side_effect = create_button

        sys.modules["game_systems.guild_system.ui.components"] = mock_components

        # Now import the module under test
        import game_systems.guild_system.ui.rank_view
        import importlib
        importlib.reload(game_systems.guild_system.ui.rank_view)
        self.rank_view_module = game_systems.guild_system.ui.rank_view

        self.mock_db = MagicMock()
        self.mock_user = MagicMock()
        self.mock_user.id = 12345
        self.mock_interaction = MagicMock()
        self.mock_interaction.user = self.mock_user
        self.mock_interaction.response = MagicMock()
        self.mock_interaction.response.is_done.return_value = False
        self.mock_interaction.response.send_message = AsyncMock()
        self.mock_interaction.response.defer = AsyncMock()
        self.mock_interaction.followup = MagicMock()
        self.mock_interaction.followup.send = AsyncMock()
        self.mock_interaction.edit_original_response = AsyncMock()
        self.mock_interaction.client = MagicMock()

    def tearDown(self):
        self.module_patcher.stop()

    def test_rank_progress_view_init(self):
        """Test RankProgressView initialization."""
        view = self.rank_view_module.RankProgressView(self.mock_db, eligible=True, interaction_user=self.mock_user)

        # Check buttons
        self.assertEqual(len(view.children), 2)
        self.assertFalse(view.children[0].disabled) # promote_btn
        self.assertEqual(view.children[0].custom_id, "req_promo")

    async def test_promote_callback_eligible(self):
        """Test promotion callback when eligible."""
        self.mock_rank_system.check_promotion_eligibility.return_value = True
        self.mock_rank_system.get_rank_info.return_value = {"rank": "F"}
        self.mock_rank_system.get_next_rank.return_value = "E"
        self.mock_rank_system.RANKS = {"E": {"title": "Recruit"}}

        view = self.rank_view_module.RankProgressView(self.mock_db, eligible=True, interaction_user=self.mock_user)

        await view.promote_callback(self.mock_interaction)

        self.mock_interaction.edit_original_response.assert_called()
        args, kwargs = self.mock_interaction.edit_original_response.call_args
        self.assertIsInstance(kwargs['view'], self.rank_view_module.RankTrialConfirmationView)

    async def test_promote_callback_not_eligible(self):
        """Test promotion callback when not eligible."""
        self.mock_rank_system.check_promotion_eligibility.return_value = False

        view = self.rank_view_module.RankProgressView(self.mock_db, eligible=True, interaction_user=self.mock_user)

        await view.promote_callback(self.mock_interaction)

        self.mock_interaction.followup.send.assert_called()
        args, kwargs = self.mock_interaction.followup.send.call_args
        self.assertIn("no longer meet", args[0])

    async def test_confirm_callback_success(self):
        """Test confirming promotion trial."""
        view = self.rank_view_module.RankTrialConfirmationView(self.mock_db, self.mock_user, "E")

        # Mock AdventureCommands Cog
        mock_cog = MagicMock()
        mock_cog.manager.start_promotion_trial = MagicMock()
        mock_cog.manager.get_active_session.return_value = {"active_monster_json": None}
        self.mock_interaction.client.get_cog.return_value = mock_cog

        # Mock DB calls inside confirm_callback
        self.mock_db.get_player_stats_json.return_value = {"strength": 10}
        self.mock_db.get_player_vitals.return_value = {"hp": 100}
        self.mock_db.get_player.return_value = {"class_id": 1}

        # Mock PlayerStats
        with patch("game_systems.player.player_stats.PlayerStats") as MockStats:
             with patch("game_systems.adventure.ui.adventure_embeds.AdventureEmbeds") as MockEmbeds:
                # Configure MockStats instance
                mock_stats_instance = MockStats.from_dict.return_value
                mock_stats_instance.max_hp = 100
                mock_stats_instance.max_mp = 50

                await view.confirm_callback(self.mock_interaction)

                mock_cog.manager.start_promotion_trial.assert_called_with(12345, "E")
                self.mock_interaction.edit_original_response.assert_called()

    async def test_confirm_callback_no_cog(self):
        """Test confirming trial when cog is missing."""
        view = self.rank_view_module.RankTrialConfirmationView(self.mock_db, self.mock_user, "E")
        self.mock_interaction.client.get_cog.return_value = None

        await view.confirm_callback(self.mock_interaction)

        self.mock_interaction.followup.send.assert_called()
        args, kwargs = self.mock_interaction.followup.send.call_args
        self.assertIn("offline", args[0])

    async def test_cancel_callback_success(self):
        """Test canceling promotion trial (returning to progress view)."""
        view = self.rank_view_module.RankTrialConfirmationView(self.mock_db, self.mock_user, "E")

        self.mock_rank_system.check_promotion_eligibility.return_value = True
        self.mock_rank_system.get_rank_info.return_value = {"rank": "F"}
        self.mock_rank_system.RANKS = {"F": {"next_rank": "E"}, "E": {"title": "Recruit"}}

        await view.cancel_callback(self.mock_interaction)

        self.mock_interaction.edit_original_response.assert_called()
        args, kwargs = self.mock_interaction.edit_original_response.call_args
        self.assertIn('embed', kwargs)
        self.assertIsInstance(kwargs['view'], self.rank_view_module.RankProgressView)


if __name__ == "__main__":
    unittest.main()
