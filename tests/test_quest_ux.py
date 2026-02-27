import os
import sys
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

# Add repo root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock discord modules BEFORE importing anything else
discord_mock = MagicMock()
discord_ui_mock = MagicMock()
sys.modules["discord"] = discord_mock
sys.modules["discord.ui"] = discord_ui_mock
sys.modules["discord.ext"] = MagicMock()
sys.modules["discord.ext.commands"] = MagicMock()

# Mock pymongo BEFORE importing DatabaseManager
sys.modules["pymongo"] = MagicMock()
sys.modules["pymongo.errors"] = MagicMock()


# Setup View and Button mocks
class MockView:
    def __init__(self, timeout=None):
        self.children = []

    def add_item(self, item):
        self.children.append(item)


discord_ui_mock.View = MockView
discord_ui_mock.Button = MagicMock
# Configure Color class mock correctly
# discord.Color is a class, so accessing discord.Color.orange returns a bound method (mock)
# calling that method should return "orange"
discord_mock.Color.gold.return_value = "gold"
discord_mock.Color.orange.return_value = "orange"

# Ensure embed.color returns the value when accessed as a property on a MagicMock
# if discord.Embed() returns a MagicMock, accessing .color on it returns a new MagicMock by default.
# We need to tell the system that if someone assigns to .color, it works (which mocks do),
# but if we assert equality, we might need to be careful.
# However, usually equality check against a mock fails unless it's configured.

# The failing test showed: AssertionError: <MagicMock name='mock.Color.orange()' ...> != 'orange'
# This means embed.color IS the return value of discord.Color.orange().
# But wait, discord.Color.orange.return_value = "orange" was set.
# Why did it return a MagicMock name='mock.Color.orange()'?
# This happens if the mock setup wasn't effective when the code ran, or if Color.orange is accessed as a property.
# In discord.py, Color.orange is a classmethod.
# Let's ensure the mock is robust.

color_mock = MagicMock()
color_mock.orange.return_value = "orange"
color_mock.gold.return_value = "gold"
discord_mock.Color = color_mock

# Now import the module under test
# Reload to ensure it picks up the mocked discord
import importlib
import game_systems.guild_system.ui.quests_menu
importlib.reload(game_systems.guild_system.ui.quests_menu)
from game_systems.guild_system.ui.quests_menu import QuestsMenuView  # noqa: E402


class TestQuestTurnInUX(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.db_mock = MagicMock()
        self.user_mock = MagicMock()
        self.user_mock.id = 12345
        self.interaction_mock = AsyncMock()
        self.interaction_mock.user = self.user_mock

    @patch("game_systems.guild_system.ui.quests_menu.QuestSystem")
    async def test_turn_in_with_incomplete_quests(self, MockQuestSystem):
        # Setup View
        view = QuestsMenuView(self.db_mock, self.user_mock)

        # Setup QuestSystem behavior
        qs_instance = MockQuestSystem.return_value

        # Mock active quests (incomplete)
        quests = [
            {
                "id": 1,
                "title": "Slime Hunt",
                "progress": {"kills": {"Slime": 3}},
                "objectives": {"kills": {"Slime": 5}},
                "status": "in_progress",
            }
        ]

        qs_instance.get_player_quests.return_value = quests
        qs_instance.check_completion.return_value = False  # None are complete

        # Manually configure the global mock directly to ensure it propagates
        # Since we control sys.modules["discord"], patching "discord.Color" might try to patch the real module if found,
        # or fail if the mock structure is complex.
        # Direct configuration is safer here.
        discord_mock.Color.orange.return_value = "orange"

        # Run callback
        with patch("cogs.quest_hub_cog.QuestLogView") as MockQuestLogView:
            await view.quest_turn_in_callback(self.interaction_mock)

        # Verify
        args, kwargs = self.interaction_mock.edit_original_response.call_args
        embed = kwargs.get("embed")

        # Assertions
        # 1. Description should contain the new narrative text
        self.assertIn("The Guildmaster reviews your report", embed.description)
        self.assertIn("Return when the work is done", embed.description)

        # 2. Color should be orange (warning)
        # We check against the return value of the mocked call to be robust
        # This passes whether it returns "orange" or a MagicMock representing "orange"
        self.assertEqual(embed.color, discord_mock.Color.orange())

        # 3. Should have added fields for the quests
        # Since embed is a mock, we check call args on add_field
        self.assertEqual(embed.add_field.call_count, 1)

        call_args = embed.add_field.call_args[1]  # kwargs
        self.assertIn("Slime Hunt", call_args["name"])
        self.assertIn("In Progress", call_args["name"])
        self.assertIn("3/5", call_args["value"])


if __name__ == "__main__":
    unittest.main()
