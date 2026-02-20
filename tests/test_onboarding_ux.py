import os
import sys
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

# --- FIX: Cleanup conflicting mocks from other tests ---
if "cogs" in sys.modules and isinstance(sys.modules["cogs"], MagicMock):
    del sys.modules["cogs"]
if "cogs.onboarding_cog" in sys.modules:
    del sys.modules["cogs.onboarding_cog"]

# Mock discord before importing cogs.onboarding_cog
sys.modules["discord"] = MagicMock()
sys.modules["discord.ui"] = MagicMock()
sys.modules["discord.ext"] = MagicMock()
sys.modules["discord.ext.commands"] = MagicMock()

# Mock PyMongo so real DatabaseManager doesn't explode
sys.modules["pymongo"] = MagicMock()
sys.modules["pymongo.errors"] = MagicMock()

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

sys.modules["discord.ui"].View = MockView
sys.modules["discord.ui"].Button = MagicMock()
sys.modules["discord.ButtonStyle"] = MagicMock()

# Add repo root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Do NOT mock database.database_manager directly to avoid breaking other tests
# sys.modules["database.database_manager"] = MagicMock()

# Import the module under test
try:
    from cogs.onboarding_cog import GuildWelcomeView, CombatTutorialView  # noqa: E402
except ImportError:
    # Fallback
    import importlib.util
    spec = importlib.util.spec_from_file_location("cogs.onboarding_cog", "cogs/onboarding_cog.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules["cogs.onboarding_cog"] = module
    spec.loader.exec_module(module)
    GuildWelcomeView = module.GuildWelcomeView
    CombatTutorialView = module.CombatTutorialView


class TestOnboardingUX(unittest.IsolatedAsyncioTestCase):
    async def test_guild_welcome_view_init(self):
        """Test that GuildWelcomeView initializes with correct buttons."""
        db = MagicMock()
        user = MagicMock()
        view = GuildWelcomeView(db, user)
        self.assertIsInstance(view, GuildWelcomeView)

    async def test_combat_tutorial_flow(self):
        """Test the state transitions of the combat tutorial."""
        db = MagicMock()
        user = MagicMock()
        view = CombatTutorialView(db, user)

        # Initial state: Step 0
        self.assertEqual(view.step, 0)

        # Prepare mock interaction
        interaction = AsyncMock()
        mock_embed = MagicMock()
        interaction.message.embeds = [mock_embed]

        # Simulate Attack (Step 0 -> 1)
        await view.attack_callback(interaction, MagicMock())
        self.assertEqual(view.step, 1)
        interaction.response.edit_message.assert_called()

        # Simulate Defend (Step 1 -> 2)
        await view.defend_callback(interaction, MagicMock())
        self.assertEqual(view.step, 2)

        # Simulate Finish (Step 2 -> 3)
        await view.finish_callback(interaction, MagicMock())
        self.assertEqual(view.step, 3)

        # Simulate Complete (Step 3 -> End)
        with patch("cogs.onboarding_cog.transition_to_guild_lobby", new_callable=AsyncMock) as mock_transition:
            await view.complete_callback(interaction, MagicMock())
            mock_transition.assert_called_with(interaction, db, user)

if __name__ == "__main__":
    unittest.main()
