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
        mock_discord.ui.Button = MagicMock()
        mock_discord.ButtonStyle = MagicMock()
        mock_discord.ext = MagicMock()
        mock_discord.ext.commands = MagicMock()

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

    def tearDown(self):
        self.modules_patcher.stop()

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
        with patch(
            "cogs.onboarding_cog.transition_to_guild_lobby", new_callable=AsyncMock
        ) as mock_transition:
            await view.complete_callback(interaction)
            mock_transition.assert_called_with(interaction, db, user)


if __name__ == "__main__":
    unittest.main()
