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


class MockEmbed:
    def __init__(self, title=None, description=None, color=None, **kwargs):
        self.title = title or ""
        self.description = description or ""
        self.color = color
        self.fields = []

    def set_footer(self, text=None):
        pass

    def add_field(self, name, value, inline=False):
        self.fields.append({"name": name, "value": value})


discord_mock.Embed.side_effect = MockEmbed


# Now import the module under test
from game_systems.guild_system.ui.quests_menu import QuestsMenuView  # noqa: E402


class TestQuestTurnInUX(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.db_mock = MagicMock()
        self.user_mock = MagicMock()
        self.user_mock.id = 12345

        import game_systems.guild_system.ui.quests_menu as quests_menu

        quests_menu.discord.Color.orange.return_value = "orange"
        quests_menu.discord.Color.green.return_value = "green"
        quests_menu.discord.Color.red.return_value = "red"
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
        # Note: We mocked Color.orange() to return "orange"
        self.assertEqual(embed.color, "orange")

        # 3. Should have added fields for the quests
        # Since embed is MockEmbed, we check fields list
        self.assertEqual(len(embed.fields), 1)

        field = embed.fields[0]
        self.assertIn("Slime Hunt", field["name"])
        self.assertIn("In Progress", field["name"])
        self.assertIn("3/5", field["value"])


if __name__ == "__main__":
    unittest.main()
