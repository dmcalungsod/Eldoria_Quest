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
        mock_discord.ui.button = lambda **kwargs: lambda func: func  # Decorator mock

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
        self.ClassDetailView = cogs.onboarding_cog.ClassDetailView
        self.CharacterMenuView = cogs.onboarding_cog.CharacterMenuView
        self.cogs_module = cogs.onboarding_cog

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

    async def test_start_menu_callback(self):
        """Test the class selection callback."""
        db = MagicMock()
        user = MagicMock()
        view = self.StartMenuView(db, user)

        interaction = AsyncMock()
        interaction.data = {"custom_id": "cls_1"}  # Warrior
        interaction.user.id = user.id

        # Mock interaction check
        check = await view.interaction_check(interaction)
        self.assertTrue(check)

        # Mock interaction response
        await view.class_select_callback(interaction)

        interaction.response.edit_message.assert_called()
        args, kwargs = interaction.response.edit_message.call_args
        self.assertIsInstance(kwargs["view"], self.ClassDetailView)
        self.assertEqual(kwargs["view"].class_id, 1)

    async def test_class_detail_view(self):
        """Test ClassDetailView creation and buttons."""
        db = MagicMock()
        user = MagicMock()
        class_id = 1
        view = self.ClassDetailView(db, class_id, user)

        # Test accept callback
        interaction = AsyncMock()
        interaction.user.id = user.id

        # Mock creator
        view.creator.create_player = MagicMock(return_value=(True, "Success"))
        db.player_exists = MagicMock(return_value=False)

        await view.create_btn(interaction, MagicMock())

        interaction.edit_original_response.assert_called()
        args, kwargs = interaction.edit_original_response.call_args
        self.assertIsInstance(kwargs["view"], self.CharacterMenuView)

    async def test_class_detail_back(self):
        """Test ClassDetailView back button."""
        db = MagicMock()
        user = MagicMock()
        view = self.ClassDetailView(db, 1, user)

        interaction = AsyncMock()
        await view.back_btn(interaction, MagicMock())

        interaction.response.edit_message.assert_called()
        args, kwargs = interaction.response.edit_message.call_args
        self.assertIsInstance(kwargs["view"], self.StartMenuView)

    async def test_character_menu_view(self):
        """Test CharacterMenuView approach_clerk."""
        db = MagicMock()
        user = MagicMock()
        view = self.CharacterMenuView(db, user)

        interaction = AsyncMock()
        await view.approach_clerk(interaction, MagicMock())

        interaction.edit_original_response.assert_called()
        args, kwargs = interaction.edit_original_response.call_args
        self.assertIsInstance(kwargs["view"], self.GuildWelcomeView)

    async def test_guild_welcome_view_init(self):
        """Test that GuildWelcomeView initializes with correct buttons."""
        db = MagicMock()
        user = MagicMock()
        view = self.GuildWelcomeView(db, user)
        self.assertIsInstance(view, self.GuildWelcomeView)

        interaction = AsyncMock()

        # Test start training
        await view.start_training(interaction, MagicMock())
        interaction.edit_original_response.assert_called()
        args, kwargs = interaction.edit_original_response.call_args
        self.assertIsInstance(kwargs["view"], self.CombatTutorialView)

        # Test skip
        interaction.reset_mock()
        with patch("cogs.onboarding_cog.transition_to_guild_lobby", new_callable=AsyncMock) as mock_trans:
            await view.skip_to_lobby(interaction, MagicMock())
            mock_trans.assert_called()

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


if __name__ == "__main__":
    unittest.main()
