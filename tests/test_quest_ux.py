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
discord_mock.Color.gold.return_value = "gold"
discord_mock.Color.orange.return_value = "orange"

# Now import the module under test
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
        # Note: We mocked Color.orange() to return "orange", but embed.color might be accessed differently depending on how Embed is constructed.
        # If embed is a MagicMock, embed.color returns a new MagicMock by default unless configured.
        # In the source code (quests_menu.py), it does `embed.color = discord.Color.orange()`.
        # Since we mocked `discord.Color.orange.return_value = "orange"`, `embed.color` should be "orange".
        # However, if embed was created via `discord.Embed(...)` which is a Mock, the constructor usage might affect it.
        # Let's verify what `embed.color` actually is.
        # The failure log said: AssertionError: <MagicMock name='mock.Color.orange()' ...> != 'orange'
        # This implies `embed.color` holds the Mock object itself, not the return value.
        # This happens if the code calls `discord.Color.orange()` (which returns the mock we set up)
        # BUT the assertion sees the mock function call result.

        # Ah, looking at the error: <MagicMock name='mock.Color.orange()' ...>
        # It seems discord.Color.orange is a MagicMock, and calling it returns a MagicMock unless we set return_value.
        # We did: discord_mock.Color.orange.return_value = "orange"

        # Re-checking the setup:
        # discord_mock.Color.gold.return_value = "gold"
        # discord_mock.Color.orange.return_value = "orange"

        # If the code uses `discord.Color.orange` (property) instead of `discord.Color.orange()` (method), that would be different.
        # Discord.py Color.orange is a classmethod, so it is called as `discord.Color.orange()`.

        # Maybe the issue is how we set up the mock.
        # discord_mock = MagicMock()
        # sys.modules["discord"] = discord_mock
        # discord_mock.Color.orange.return_value = "orange"

        # If I look at the error again: <MagicMock name='mock.Color.orange()' id='140098889106400'>
        # The name suggests it's the result of calling orange().

        # Let's relax the assertion to check if it's the right thing, or ensure the mock returns a string.
        # It's possible the `Color` class itself needs to be mocked differently.

        # If the code does: `embed.color = discord.Color.orange()`
        # And we set `discord.Color.orange.return_value = 'orange'`
        # Then `embed.color` should be `'orange'`.

        # Wait, if `discord.Color` is a MagicMock, `discord.Color.orange` is a child MagicMock.
        # `discord.Color.orange()` returns `discord.Color.orange.return_value`.

        # Let's force it in the test function to be sure.
        self.assertEqual(embed.color, "orange")

        # 3. Should have added fields for the quests
        # Since embed is a mock, we check call args on add_field
        self.assertEqual(embed.add_field.call_count, 1)

        call_args = embed.add_field.call_args[1]  # kwargs
        self.assertIn("Slime Hunt", call_args["name"])
        self.assertIn("In Progress", call_args["name"])
        self.assertIn("3/5", call_args["value"])


if __name__ == "__main__":
    unittest.main()
