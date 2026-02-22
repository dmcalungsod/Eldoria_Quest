import importlib
import os
import sys
import unittest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch

# Add repo root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestHelpCommand(unittest.TestCase):
    def setUp(self):
        self.modules_patcher = patch.dict(sys.modules)
        self.modules_patcher.start()

        # Setup Mocks
        self.mock_discord = MagicMock()

        # Mock View
        class MockView:
            def __init__(self, timeout=None):
                self.timeout = timeout
                self.children = []
                self.view = self
            def add_item(self, item):
                self.children.append(item)
                item.view = self # Mimic discord.ui behavior
            async def interaction_check(self, interaction):
                return True

        # Mock Select
        class MockSelect:
            def __init__(self, placeholder=None, min_values=1, max_values=1, options=None, row=None):
                self.placeholder = placeholder
                self.options = options or []
                self.values = []
                self.view = None

            async def callback(self, interaction):
                pass

        self.mock_discord.ui.View = MockView
        self.mock_discord.ui.Select = MockSelect
        # Ensure SelectOption works as a constructor that stores attributes
        def mock_select_option(label, description=None, emoji=None):
            m = MagicMock()
            m.label = label
            m.description = description
            m.emoji = emoji
            return m

        self.mock_discord.SelectOption = mock_select_option

        sys.modules["discord"] = self.mock_discord
        sys.modules["discord.ui"] = self.mock_discord.ui
        sys.modules["discord.ext"] = MagicMock()

        # Reload module
        import cogs.general_cog
        importlib.reload(cogs.general_cog)
        self.general_cog = cogs.general_cog

    def tearDown(self):
        self.modules_patcher.stop()

    def test_help_view_initialization(self):
        user = MagicMock()
        user.id = 123
        view = self.general_cog.HelpView(user)

        # Check if Select menu is added
        self.assertEqual(len(view.children), 1)
        select = view.children[0]
        self.assertIsInstance(select, self.general_cog.HelpSelect)

        # Check options
        labels = [opt.label for opt in select.options]
        expected_labels = [
            "Getting Started",
            "Commands",
            "Guild & Quests",
            "Combat & Exploration",
            "Character Progression"
        ]
        self.assertEqual(sorted(labels), sorted(expected_labels))

    def test_interaction_check_success(self):
        user = MagicMock()
        user.id = 123
        view = self.general_cog.HelpView(user)

        interaction = MagicMock()
        interaction.user.id = 123

        async def run_test():
            result = await view.interaction_check(interaction)
            self.assertTrue(result)

        asyncio.run(run_test())

    def test_interaction_check_failure(self):
        user = MagicMock()
        user.id = 123
        view = self.general_cog.HelpView(user)

        interaction = MagicMock()
        interaction.user.id = 456
        interaction.response.send_message = AsyncMock()

        async def run_test():
            result = await view.interaction_check(interaction)
            self.assertFalse(result)
            # Verify ephemeral message sent
            interaction.response.send_message.assert_called_with("This manual is not for you.", ephemeral=True)

        asyncio.run(run_test())

    def test_select_callback(self):
        user = MagicMock()
        view = self.general_cog.HelpView(user)
        select = view.children[0]

        interaction = MagicMock()
        interaction.response.edit_message = AsyncMock()

        # Test "Getting Started"
        select.values = ["Getting Started"]

        async def run_test():
            await select.callback(interaction)

            # Check that edit_message was called with an Embed
            args, kwargs = interaction.response.edit_message.call_args
            embed = kwargs.get('embed')
            self.assertIsNotNone(embed)
            self.assertEqual(embed.title, "🌱 Getting Started")

        asyncio.run(run_test())

if __name__ == "__main__":
    unittest.main()
