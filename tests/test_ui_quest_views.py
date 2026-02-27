import importlib
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
        self.values = []  # For Select

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

    async def interaction_check(self, interaction):
        return True

# Mock discord module
mock_discord = MagicMock()
mock_discord.ButtonStyle = MagicMock()
mock_discord.Color = MagicMock()
mock_discord.ui.View = MockView
mock_discord.ui.Button = MockButton
mock_discord.ui.Select = MockSelect
sys.modules["discord"] = mock_discord
sys.modules["discord.ui"] = mock_discord.ui
sys.modules["discord.ext"] = MagicMock()
sys.modules["discord.ext.commands"] = MagicMock()

# Import after mocking
if "cogs" not in sys.modules:
    sys.modules["cogs"] = MagicMock()
if "cogs.utils" not in sys.modules:
    sys.modules["cogs.utils"] = MagicMock()
if "cogs.utils.ui_helpers" not in sys.modules:
    sys.modules["cogs.utils.ui_helpers"] = MagicMock()
if "cogs.quest_hub_cog" not in sys.modules:
    sys.modules["cogs.quest_hub_cog"] = MagicMock()

import game_systems.guild_system.ui.quests_menu
importlib.reload(game_systems.guild_system.ui.quests_menu)
from game_systems.guild_system.ui.quests_menu import QuestsMenuView

# Important: We need to reload cogs.quest_hub_cog if it was already imported,
# or import it properly now that mocks are in place.

# Force unload cogs.quest_hub_cog if it exists to ensure a fresh import with our mocked discord
if "cogs.quest_hub_cog" in sys.modules:
    del sys.modules["cogs.quest_hub_cog"]

# Ensure cogs is treated as a package
if "cogs" not in sys.modules:
    sys.modules["cogs"] = MagicMock()

# Since imports in python are cached, and we messed with sys.modules,
# we need to force reload cogs.quest_hub_cog from file
import types
loader = importlib.machinery.SourceFileLoader('cogs.quest_hub_cog', os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'cogs/quest_hub_cog.py'))
quest_hub_cog = types.ModuleType(loader.name)
loader.exec_module(quest_hub_cog)
sys.modules['cogs.quest_hub_cog'] = quest_hub_cog

from cogs.quest_hub_cog import QuestBoardView, QuestDetailView, QuestLedgerView, QuestLogView

class TestQuestViews(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.mock_db = MagicMock()
        self.mock_user = MagicMock()
        self.mock_user.id = 12345
        self.mock_interaction = AsyncMock()
        self.mock_interaction.user = self.mock_user
        self.mock_interaction.response = AsyncMock()
        self.mock_interaction.response.is_done.return_value = False

    def test_ledger_view_init(self):
        """Test QuestLedgerView initialization."""
        active_quests = [{"id": 1, "title": "Test Quest"}]
        view = QuestLedgerView(self.mock_db, active_quests, self.mock_user)

        # Check back button exists
        self.assertEqual(len(view.children), 1)
        self.assertEqual(view.children[0].label, "Back to Guild Hall")

    async def test_ledger_view_interaction_check(self):
        """Test interaction check."""
        view = QuestLedgerView(self.mock_db, [], self.mock_user)

        # Correct user
        result = await view.interaction_check(self.mock_interaction)
        self.assertTrue(result)

        # Incorrect user
        other_user = MagicMock()
        other_user.id = 999
        self.mock_interaction.user = other_user

        # View's interaction_check behavior: if mismatch, sends ephemeral message and returns False
        result = await view.interaction_check(self.mock_interaction)
        self.assertFalse(result)
        self.mock_interaction.response.send_message.assert_called_with("This is not your adventure.", ephemeral=True)

    @patch("cogs.quest_hub_cog.QuestSystem")
    def test_quest_log_view_init(self, MockQuestSystem):
        """Test QuestLogView initialization with completable quests."""
        # Setup mock system
        mock_system = MockQuestSystem.return_value
        mock_system.check_completion.return_value = True  # All quests completable

        active_quests = [{"id": 1, "title": "Q1", "progress": {}, "objectives": {}}]

        view = QuestLogView(self.mock_db, active_quests, self.mock_user)

        # Should have back button and select menu
        self.assertEqual(len(view.children), 2)

        # Select menu should have options
        # Note: children order depends on implementation. Usually back button added first in __init__?
        # In QuestLogView: back_button added, then quest_select added.
        select = view.children[1]
        self.assertEqual(len(select.options), 1)
        self.assertEqual(select.options[0].value, "1")
        self.assertFalse(select.disabled)

    @patch("cogs.quest_hub_cog.QuestSystem")
    def test_quest_log_view_init_empty(self, MockQuestSystem):
        """Test QuestLogView initialization with no completable quests."""
        mock_system = MockQuestSystem.return_value
        mock_system.check_completion.return_value = False

        active_quests = [{"id": 1, "title": "Q1", "progress": {}, "objectives": {}}]

        view = QuestLogView(self.mock_db, active_quests, self.mock_user)

        select = view.children[1]
        self.assertTrue(select.disabled)
        self.assertEqual(select.options[0].value, "disabled")

    @patch("cogs.quest_hub_cog.QuestSystem")
    async def test_complete_quest_callback(self, MockQuestSystem):
        """Test completing a quest."""
        mock_system = MockQuestSystem.return_value
        mock_system.complete_quest.return_value = (True, "Reward!")
        mock_system.get_player_quests.return_value = []  # No more quests

        active_quests = [{"id": 1, "title": "Q1", "progress": {}, "objectives": {}}]
        view = QuestLogView(self.mock_db, active_quests, self.mock_user)

        # Simulate selection
        view.quest_select.values = ["1"]

        # Prepare interaction message embed
        mock_embed = MagicMock()
        self.mock_interaction.message.embeds = [mock_embed]

        await view.complete_quest_callback(self.mock_interaction)

        # Verify complete_quest called
        mock_system.complete_quest.assert_called_with(12345, 1)

        # Verify embed updated
        self.mock_interaction.edit_original_response.assert_called()
        args, kwargs = self.mock_interaction.edit_original_response.call_args
        self.assertEqual(kwargs["embed"], mock_embed)

    @patch("cogs.quest_hub_cog.QuestSystem")
    def test_quest_board_view_init(self, MockQuestSystem):
        """Test QuestBoardView initialization."""
        quests = [{"id": 1, "title": "Q1", "tier": "F", "summary": "Desc"}]

        view = QuestBoardView(self.mock_db, quests, self.mock_user)

        # In QuestBoardView: quest_select added first, then back_button
        select = view.children[0]
        self.assertFalse(select.disabled)
        self.assertEqual(len(select.options), 1)
        self.assertEqual(select.options[0].value, "1")

    @patch("cogs.quest_hub_cog.QuestSystem")
    async def test_view_quest_details_callback(self, MockQuestSystem):
        """Test viewing quest details."""
        mock_system = MockQuestSystem.return_value
        mock_system.get_quest_details.return_value = {
            "title": "Q1",
            "description": "Desc",
            "objectives": {"kill": {"slime": 5}},
            "rewards": {"gold": 10},
            "tier": "F",
        }

        quests = [{"id": 1, "tier": "F", "title": "Q1", "summary": "Summary"}]
        view = QuestBoardView(self.mock_db, quests, self.mock_user)
        view.quest_select.values = ["1"]

        await view.view_quest_details_callback(self.mock_interaction)

        # Verify interaction response
        self.mock_interaction.edit_original_response.assert_called()
        args, kwargs = self.mock_interaction.edit_original_response.call_args

        # Check if new view is QuestDetailView
        self.assertIsInstance(kwargs["view"], QuestDetailView)
        self.assertEqual(kwargs["view"].quest_id, 1)

    @patch("cogs.quest_hub_cog.QuestSystem")
    async def test_accept_quest_callback(self, MockQuestSystem):
        """Test accepting a quest."""
        mock_system = MockQuestSystem.return_value
        mock_system.accept_quest.return_value = True
        mock_system.get_available_quests.return_value = []

        view = QuestDetailView(self.mock_db, 1, [], self.mock_user)

        await view.accept_quest_callback(self.mock_interaction)

        mock_system.accept_quest.assert_called_with(12345, 1)

        # Should transition back to board
        self.mock_interaction.edit_original_response.assert_called()
        args, kwargs = self.mock_interaction.edit_original_response.call_args
        self.assertIsInstance(kwargs["view"], QuestBoardView)

    async def test_quests_menu_view_callbacks(self):
        """Test QuestsMenuView navigation callbacks."""
        view = QuestsMenuView(self.mock_db, self.mock_user)

        # Since QuestsMenuView does 'from cogs.quest_hub_cog import QuestBoardView' inside the method,
        # we need to patch it in 'cogs.quest_hub_cog'.

        # Test view_quests_callback
        with patch("game_systems.guild_system.ui.quests_menu.QuestSystem") as MockQS:
            MockQS.return_value.get_available_quests.return_value = []

            # Patch in the module where the class is defined
            with patch("cogs.quest_hub_cog.QuestBoardView") as MockBoardView:
                await view.view_quests_callback(self.mock_interaction)
                self.mock_interaction.edit_original_response.assert_called()
                args, kwargs = self.mock_interaction.edit_original_response.call_args
                self.assertEqual(kwargs["view"], MockBoardView.return_value)

        # Test view_quest_ledger_callback
        with patch("game_systems.guild_system.ui.quests_menu.QuestSystem") as MockQS:
            MockQS.return_value.get_player_quests.return_value = []
            with patch("cogs.quest_hub_cog.QuestLedgerView") as MockLedgerView:
                await view.view_quest_ledger_callback(self.mock_interaction)
                self.mock_interaction.edit_original_response.assert_called()
                args, kwargs = self.mock_interaction.edit_original_response.call_args
                self.assertEqual(kwargs["view"], MockLedgerView.return_value)

        # Test quest_turn_in_callback
        with patch("game_systems.guild_system.ui.quests_menu.QuestSystem") as MockQS:
            MockQS.return_value.get_player_quests.return_value = []
            with patch("cogs.quest_hub_cog.QuestLogView") as MockLogView:
                await view.quest_turn_in_callback(self.mock_interaction)
                self.mock_interaction.edit_original_response.assert_called()
                args, kwargs = self.mock_interaction.edit_original_response.call_args
                self.assertEqual(kwargs["view"], MockLogView.return_value)


if __name__ == "__main__":
    unittest.main()
