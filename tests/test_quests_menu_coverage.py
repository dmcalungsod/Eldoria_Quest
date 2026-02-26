import importlib
import os
import sys
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

# Configure sys.modules with mocks FIRST
mock_pymongo = MagicMock()
mock_pymongo.errors = MagicMock()
sys.modules["pymongo"] = mock_pymongo
sys.modules["pymongo.errors"] = mock_pymongo.errors

mock_discord = MagicMock()
mock_discord.ButtonStyle.primary = "primary"
mock_discord.ButtonStyle.secondary = "secondary"
mock_discord.ButtonStyle.grey = "grey"
mock_discord.ButtonStyle.success = "success"
mock_discord.Color.dark_green.return_value = "dark_green"
mock_discord.Color.gold.return_value = "gold"

mock_ui = MagicMock()


class MockView:
    def __init__(self, timeout=None):
        self.children = []

    def add_item(self, item):
        self.children.append(item)


mock_ui.View = MockView


class MockButton:
    def __init__(self, label=None, style=None, custom_id=None, row=None, emoji=None, callback=None, disabled=False):
        self.label = label
        self.style = style
        self.custom_id = custom_id
        self.row = row
        self.emoji = emoji
        self.callback = callback
        self.disabled = disabled


mock_ui.Button = MockButton

sys.modules["discord"] = mock_discord
sys.modules["discord.ui"] = mock_ui

# Add repo root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# Mock out dependencies to prevent recursive imports failing during tests
class MockQuestSystem:
    def __init__(self, db):
        pass


sys.modules["game_systems.guild_system.quest_system"] = MagicMock()
sys.modules["game_systems.guild_system.quest_system"].QuestSystem = MockQuestSystem


class MockQuestBoardView(MockView):
    def __init__(self, db, quests, user):
        super().__init__()
        self.set_back_button = MagicMock()


class MockQuestLedgerView(MockView):
    def __init__(self, db, quests, user):
        super().__init__()
        self.set_back_button = MagicMock()


class MockQuestLogView(MockView):
    def __init__(self, db, quests, user):
        super().__init__()
        self.set_back_button = MagicMock()


sys.modules["cogs.quest_hub_cog"] = MagicMock()
sys.modules["cogs.quest_hub_cog"].QuestBoardView = MockQuestBoardView
sys.modules["cogs.quest_hub_cog"].QuestLedgerView = MockQuestLedgerView
sys.modules["cogs.quest_hub_cog"].QuestLogView = MockQuestLogView

import game_systems.guild_system.ui.quests_menu  # noqa: E402

importlib.reload(game_systems.guild_system.ui.quests_menu)
from game_systems.guild_system.ui.quests_menu import QuestsMenuView  # noqa: E402


class MockEmbed:
    def __init__(self, title=None, description=None, color=None):
        self.title = title or ""
        self.description = description or ""
        self.color = color
        self.fields = []

    def set_footer(self, text=None):
        pass

    def add_field(self, name, value, inline=False):
        self.fields.append({"name": name, "value": value})


mock_discord.Embed.side_effect = MockEmbed


class TestQuestsMenuViewCoverage(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.mock_db = MagicMock()
        self.mock_user = MagicMock()
        self.mock_user.id = 12345

        # Patch make_progress_bar since we know it works
        self.patcher_pb = patch("game_systems.guild_system.ui.quests_menu.make_progress_bar", return_value="[###---]")
        self.mock_pb = self.patcher_pb.start()

    def tearDown(self):
        self.patcher_pb.stop()

    def test_format_progress_dict_objectives(self):
        quest = {
            "title": "Clear Cave",
            "objectives": {"slay": {"Bat": 5, "Spider": 3}},
            "progress": {"slay": {"Bat": 5, "Spider": 1}},
        }

        lines = QuestsMenuView._format_progress(quest)
        self.assertEqual(len(lines), 2)
        self.assertIn("Bat: `[###---]` 5/5", lines[0])
        self.assertIn("Spider: `[###---]` 1/3", lines[1])

    def test_format_progress_scalar_objective(self):
        quest = {"title": "Explore Cave", "objectives": {"explore": "Cavern"}, "progress": {"explore": {"Cavern": 1}}}

        lines = QuestsMenuView._format_progress(quest)
        self.assertEqual(len(lines), 1)
        self.assertIn("Explore Cavern: `[###---]` 1/1", lines[0])

    def test_format_progress_missing_data(self):
        # Progress dictionary is missing the objective key completely
        quest = {"title": "Missing Progress", "objectives": {"slay": {"Goblin": 5}}, "progress": {}}

        lines = QuestsMenuView._format_progress(quest)
        self.assertEqual(len(lines), 1)
        self.assertIn("Goblin: `[###---]` 0/5", lines[0])

        quest_no_prog_data = {"title": "No Progress Data at all", "objectives": {"slay": {"Goblin": 5}}}
        lines = QuestsMenuView._format_progress(quest_no_prog_data)
        self.assertEqual(len(lines), 1)
        self.assertIn("0/5", lines[0])

    async def test_view_quests_callback(self):
        view = QuestsMenuView(self.mock_db, self.mock_user)
        interaction = AsyncMock()

        with patch("game_systems.guild_system.ui.quests_menu.QuestSystem") as MockQuestSysCls:
            mock_sys = MockQuestSysCls.return_value
            mock_sys.get_available_quests.return_value = [{"id": 1, "title": "Help"}]

            await view.view_quests_callback(interaction)

            mock_sys.get_available_quests.assert_called_with(12345)
            interaction.edit_original_response.assert_called_once()

            # Verify view passed to edit
            kwargs = interaction.edit_original_response.call_args[1]
            self.assertIsInstance(kwargs["view"], MockQuestBoardView)
            self.assertEqual(kwargs["view"].set_back_button.call_count, 1)

    async def test_view_quest_ledger_callback_with_quests(self):
        view = QuestsMenuView(self.mock_db, self.mock_user)
        interaction = AsyncMock()

        quests = [{"id": 1, "title": "Help", "objectives": {"slay": {"Rat": 5}}, "progress": {}}]

        with patch("game_systems.guild_system.ui.quests_menu.QuestSystem") as MockQuestSysCls:
            mock_sys = MockQuestSysCls.return_value
            mock_sys.get_player_quests.return_value = quests

            await view.view_quest_ledger_callback(interaction)

            kwargs = interaction.edit_original_response.call_args[1]
            embed = kwargs["embed"]
            self.assertEqual(embed.fields[0]["name"], "Help")
            self.assertEqual(kwargs["view"].set_back_button.call_count, 1)

    async def test_view_quest_ledger_callback_empty(self):
        view = QuestsMenuView(self.mock_db, self.mock_user)
        interaction = AsyncMock()

        with patch("game_systems.guild_system.ui.quests_menu.QuestSystem") as MockQuestSysCls:
            mock_sys = MockQuestSysCls.return_value
            mock_sys.get_player_quests.return_value = []

            await view.view_quest_ledger_callback(interaction)

            kwargs = interaction.edit_original_response.call_args[1]
            embed = kwargs["embed"]
            self.assertEqual(embed.fields[0]["name"], "No Active Contracts")


if __name__ == "__main__":
    unittest.main()
