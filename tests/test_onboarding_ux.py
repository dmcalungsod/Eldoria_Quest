import importlib
import os
import sys
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

# Add repo root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# Mock View for inheritance
class MockView:
    def __init__(self, timeout=None):
        self.timeout = timeout
        self.children = []

    def add_item(self, item):
        self.children.append(item)

    def clear_items(self):
        self.children = []

    async def interaction_check(self, interaction):
        return True


class TestOnboardingUX(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        # Patch sys.modules
        self.modules_patcher = patch.dict(sys.modules)
        self.modules_patcher.start()

        # Mock discord
        mock_discord = MagicMock()
        mock_discord.ui.View = MockView

        class MockButton:
            def __init__(self, label=None, custom_id=None, emoji=None, style=None):
                self.label = label
                self.custom_id = custom_id
                self.emoji = emoji
                self.style = style
                self.callback = None

        mock_discord.ui.Button = MockButton
        mock_discord.ButtonStyle = MagicMock()
        mock_discord.ext = MagicMock()
        mock_discord.ext.commands = MagicMock()

        # Preserve functions decorated with @discord.ui.button and @app_commands.command
        def fake_button_decorator(*args, **kwargs):
            def decorator(func):
                func.__ui_button__ = kwargs
                return func

            return decorator

        def fake_app_command_decorator(*args, **kwargs):
            def decorator(func):
                func.callback = func
                return func

            return decorator

        mock_discord.ui.button = fake_button_decorator

        class MockAppCommands:
            def command(self, *args, **kwargs):
                return fake_app_command_decorator(*args, **kwargs)

        class MockCog:
            pass

        mock_discord.app_commands = MockAppCommands()
        mock_discord.ext.commands.Cog = MockCog

        sys.modules["discord"] = mock_discord
        sys.modules["discord.ui"] = mock_discord.ui
        sys.modules["discord.ext"] = mock_discord.ext
        sys.modules["discord.ext.commands"] = mock_discord.ext.commands

        # Mock PyMongo
        mock_pymongo = MagicMock()
        mock_pymongo.errors = MagicMock()
        sys.modules["pymongo"] = mock_pymongo
        sys.modules["pymongo.errors"] = mock_pymongo.errors

        # Import modules under test
        import cogs.onboarding_cog

        importlib.reload(cogs.onboarding_cog)

        self.GuildWelcomeView = cogs.onboarding_cog.GuildWelcomeView
        self.CombatTutorialView = cogs.onboarding_cog.CombatTutorialView
        self.StartMenuView = cogs.onboarding_cog.StartMenuView

    def tearDown(self):
        self.modules_patcher.stop()

    async def test_start_menu_view_init(self):
        """Test that StartMenuView initializes with class buttons containing emojis."""
        db = MagicMock()
        user = MagicMock()
        view = self.StartMenuView(db, user)

        # Check if buttons are created
        self.assertTrue(len(view.children) > 0, "No buttons created in StartMenuView")

        # Verify buttons have emojis
        mock_discord = sys.modules["discord"]
        for btn in view.children:
            self.assertIsNotNone(btn.emoji, f"Button {btn.label} is missing an emoji")
            self.assertEqual(btn.style, mock_discord.ButtonStyle.primary, f"Button {btn.label} has wrong style")

    async def test_guild_welcome_view_init(self):
        """Test that GuildWelcomeView initializes with correct buttons."""
        db = MagicMock()
        user = MagicMock()
        view = self.GuildWelcomeView(db, user)
        self.assertIsInstance(view, self.GuildWelcomeView)

    async def test_combat_tutorial_flow(self):
        """Test the state transitions of the combat tutorial."""
        db = MagicMock()
        user = MagicMock()
        view = self.CombatTutorialView(db, user)

        # Initial state: Step 0
        self.assertEqual(view.step, 0)

        # Prepare mock interaction
        interaction = AsyncMock()
        mock_embed = MagicMock()
        interaction.message.embeds = [mock_embed]

        # Simulate Attack (Step 0 -> 1)
        await view.attack_callback(interaction)
        self.assertEqual(view.step, 1)
        interaction.response.edit_message.assert_called()

        # Simulate Defend (Step 1 -> 2)
        await view.defend_callback(interaction)
        self.assertEqual(view.step, 2)

        # Simulate Finish (Step 2 -> 3)
        await view.finish_callback(interaction)
        self.assertEqual(view.step, 3)

        # Simulate Complete (Step 3 -> End)
        with patch("cogs.onboarding_cog.transition_to_guild_lobby", new_callable=AsyncMock) as mock_transition:
            await view.complete_callback(interaction)
            mock_transition.assert_called_with(interaction, db, user)

    @patch("cogs.onboarding_cog.PlayerCreator")
    @patch("cogs.onboarding_cog.CharacterMenuView")
    async def test_class_detail_view_create_btn(self, MockCharacterMenuView, MockPlayerCreator):
        import cogs.onboarding_cog

        db = MagicMock()
        user = MagicMock()
        user.display_name = "Hero"
        view = cogs.onboarding_cog.ClassDetailView(db, class_id=1, user=user)

        # Mock PlayerCreator
        creator_instance = MockPlayerCreator.return_value
        creator_instance.create_player.return_value = (True, "Success")

        # Test Player already exists
        db.player_exists.return_value = True
        interaction = AsyncMock()
        await view.create_btn(interaction, None)
        interaction.followup.send.assert_called_with("You already have a character!", ephemeral=True)

        # Test successful creation
        db.player_exists.return_value = False
        interaction2 = AsyncMock()
        await view.create_btn(interaction2, None)
        interaction2.edit_original_response.assert_called_once()

        # Test failed creation
        creator_instance.create_player.return_value = (False, "Failure")
        interaction3 = AsyncMock()
        await view.create_btn(interaction3, None)
        interaction3.followup.send.assert_called()

    @patch("cogs.onboarding_cog.StartMenuView")
    async def test_class_detail_view_back_btn(self, MockStartMenuView):
        import cogs.onboarding_cog

        db = MagicMock()
        user = MagicMock()
        view = cogs.onboarding_cog.ClassDetailView(db, class_id=1, user=user)
        interaction = AsyncMock()
        await view.back_btn(interaction, None)
        interaction.response.edit_message.assert_called_once()

    @patch("cogs.onboarding_cog.GuildWelcomeView")
    async def test_character_menu_view_approach_clerk(self, MockGuildWelcomeView):
        import cogs.onboarding_cog

        db = MagicMock()
        user = MagicMock()
        view = cogs.onboarding_cog.CharacterMenuView(db, user)
        interaction = AsyncMock()
        await view.approach_clerk(interaction, None)
        interaction.edit_original_response.assert_called_once()

    async def test_interaction_checks(self):
        import cogs.onboarding_cog

        db = MagicMock()
        user = MagicMock()
        user.id = 123

        bad_interaction = AsyncMock()
        bad_interaction.user.id = 999

        views = [
            cogs.onboarding_cog.StartMenuView(db, user),
            cogs.onboarding_cog.ClassDetailView(db, 1, user),
            cogs.onboarding_cog.CharacterMenuView(db, user),
            cogs.onboarding_cog.GuildWelcomeView(db, user),
            cogs.onboarding_cog.CombatTutorialView(db, user),
        ]

        for view in views:
            # We must await the check
            result = await view.interaction_check(bad_interaction)
            self.assertFalse(result)

    async def test_onboarding_cog_start_command(self):
        import cogs.onboarding_cog

        bot = MagicMock()
        cog = cogs.onboarding_cog.OnboardingCog(bot)
        cog.db = MagicMock()

        interaction = AsyncMock()
        interaction.user.id = 123

        # Test new player
        cog.db.player_exists.return_value = False
        with patch("cogs.onboarding_cog.StartMenuView") as MockStartMenuView:
            await cog.start(interaction)
            interaction.response.send_message.assert_called_once()

        # Test existing player
        cog.db.player_exists.return_value = True
        interaction2 = AsyncMock()
        with patch("cogs.onboarding_cog.back_to_profile_callback", new_callable=AsyncMock) as mock_back:
            await cog.start(interaction2)
            mock_back.assert_called_once()


if __name__ == "__main__":
    unittest.main()
