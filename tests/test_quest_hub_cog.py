import os
import sys
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

# Add repo root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock PyMongo globally
sys.modules["pymongo"] = MagicMock()
sys.modules["pymongo.errors"] = MagicMock()

# Mock discord globally
mock_discord = MagicMock()
mock_discord.Color.gold.return_value = "gold"
mock_discord.Color.green.return_value = "green"
mock_discord.Color.red.return_value = "red"


class MockView:
    def __init__(self, timeout=None):
        self.children = []
        self.timeout = timeout

    def add_item(self, item):
        self.children.append(item)


mock_discord.ui.View = MockView


class MockButton:
    def __init__(self, label=None, style=None, custom_id=None, emoji=None, row=None, disabled=False, callback=None):
        self.label = label
        self.style = style
        self.custom_id = custom_id
        self.emoji = emoji
        self.row = row
        self.disabled = disabled
        self.callback = callback


mock_discord.ui.Button = MockButton
sys.modules["discord"] = mock_discord
sys.modules["discord.ui"] = mock_discord.ui
sys.modules["discord.ext"] = MagicMock()
sys.modules["discord.ext.commands"] = MagicMock()


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


mock_discord.Embed.side_effect = MockEmbed


# (Imports moved to setUp to prevent test pollution)


class TestQuestHubCog(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.db = MagicMock()
        self.user = MagicMock()
        self.user.id = 12345
        self.user.name = "Hero"

        self.interaction = AsyncMock()
        self.interaction.user = self.user

        # Explicit Mock config for quest_hub_cog discord instance
        # Re-assert module mocks before dynamically loading quest hub cog
        self.old_discord_ui = sys.modules.get("discord.ui")
        self.old_cogs_quest = sys.modules.get("cogs.quest_hub_cog")

        sys.modules["discord.ui"] = mock_discord.ui
        if "cogs.quest_hub_cog" in sys.modules:
            del sys.modules["cogs.quest_hub_cog"]
        import cogs.quest_hub_cog as qhc

        qhc.discord.Color.green.return_value = "green"
        qhc.discord.Color.red.return_value = "red"
        qhc.discord.Color.gold.return_value = "gold"
        qhc.discord.Embed.side_effect = MockEmbed
        qhc.discord.ui.Button = MockButton

        self.QuestLogView = qhc.QuestLogView
        self.QuestHubCog = qhc.QuestHubCog
        self.QuestBoardView = qhc.QuestBoardView
        self.QuestDetailView = qhc.QuestDetailView

    def tearDown(self):
        if self.old_discord_ui:
            sys.modules["discord.ui"] = self.old_discord_ui
        else:
            sys.modules.pop("discord.ui", None)

        if self.old_cogs_quest:
            sys.modules["cogs.quest_hub_cog"] = self.old_cogs_quest
        else:
            sys.modules.pop("cogs.quest_hub_cog", None)

    @patch("cogs.quest_hub_cog.QuestSystem")
    async def test_quest_log_view_complete_callback_disabled(self, MockQuestSystem):
        """Test complete button disabled on missing quest."""
        quests = [{"id": 1, "status": "completed", "title": "Test Quest 1", "progress": {}, "objectives": {}}]
        qs_instance = MockQuestSystem.return_value
        qs_instance.verify_quest_requirements.return_value = (True, "")

        view = self.QuestLogView(self.db, quests, self.user)

        # Manually alter the selected values state
        view.quest_select = MagicMock()
        view.quest_select.values = []

        await view.complete_quest_callback(self.interaction)

        self.interaction.followup.send.assert_called_with("Invalid selection.", ephemeral=True)

    @patch("cogs.quest_hub_cog.QuestSystem")
    async def test_quest_log_view_complete_callback_error(self, MockQuestSystem):
        """Test complete button path that yields an error during turn-in."""
        quests = [{"id": 1, "status": "completed", "title": "Test Quest 1", "progress": {}, "objectives": {}}]

        qs_instance = MockQuestSystem.return_value
        qs_instance.verify_quest_requirements.return_value = (False, "Missing items")
        qs_instance.complete_quest.return_value = (False, "Missing items")

        view = self.QuestLogView(self.db, quests, self.user)
        view.quest_select = MagicMock()
        view.quest_select.values = ["1"]  # Select ID 1

        await view.complete_quest_callback(self.interaction)

        # Should fetch new quests and edit the original message since error happened
        args, kwargs = self.interaction.edit_original_response.call_args
        embed = kwargs.get("embed")

        self.assertIn("Missing items", embed.description)
        self.assertEqual(embed.color, "red")

    @patch("cogs.quest_hub_cog.QuestSystem")
    async def test_quest_log_view_complete_callback_success(self, MockQuestSystem):
        """Test a fully successful turn-in."""
        quests = [{"id": 1, "status": "completed", "title": "Test Quest 1", "progress": {}, "objectives": {}}]

        qs_instance = MockQuestSystem.return_value
        qs_instance.verify_quest_requirements.return_value = (True, "")
        qs_instance.complete_quest.return_value = (True, "Quest Turned In!")
        qs_instance.get_player_quests.return_value = []

        view = self.QuestLogView(self.db, quests, self.user)
        view.quest_select = MagicMock()
        view.quest_select.values = ["1"]

        await view.complete_quest_callback(self.interaction)

        # Check embed attributes
        args, kwargs = self.interaction.edit_original_response.call_args
        embed = kwargs.get("embed")

        self.assertIn("Quest Turned In!", embed.description)
        self.assertEqual(embed.color, "gold")

    async def test_quest_log_view_interaction_check(self):
        """Test that the view rejects interactions from other users."""
        quests = []
        view = self.QuestLogView(self.db, quests, self.user)

        bad_interaction = AsyncMock()
        bad_interaction.user.id = 999

        result = await view.interaction_check(bad_interaction)
        self.assertFalse(result)
        bad_interaction.response.send_message.assert_called_with("This is not your adventure.", ephemeral=True)

        good_interaction = AsyncMock()
        good_interaction.user.id = 12345
        result = await view.interaction_check(good_interaction)
        self.assertTrue(result)

    async def test_quest_log_view_set_back_button(self):
        """Test overriding the back button callback."""
        quests = []
        view = self.QuestLogView(self.db, quests, self.user)

        async def dummy_cb(interaction):
            pass

        view.set_back_button(dummy_cb, label="Go Back!")

        back_btn = next((b for b in view.children if b.custom_id == "back_to_profile"), None)
        self.assertIsNotNone(back_btn)
        self.assertEqual(back_btn.label, "Go Back!")
        # Can't directly compare callback since discord.ui wraps it, but we can verify it was created
        self.assertTrue(hasattr(back_btn, "callback"))

    @patch("cogs.quest_hub_cog.QuestSystem")
    async def test_quest_board_view_quest_details_callback(self, MockQuestSystem):
        """Test QuestBoardView viewing details of a quest."""
        quests = [{"id": 1, "title": "Test Quest", "tier": "E", "summary": "A test"}]

        view = self.QuestBoardView(self.db, quests, self.user)
        view.quest_select = MagicMock()
        view.quest_select.values = ["1"]

        qs_instance = MockQuestSystem.return_value
        qs_instance.get_quest_details.return_value = {
            "title": "Test Quest",
            "description": "Details",
            "tier": "E",
            "objectives": {"kills": "5 Slimes"},
            "rewards": {"aurum": 50},
        }

        with patch("cogs.quest_hub_cog.QuestDetailView", autospec=True) as MockDetailView:
            await view.view_quest_details_callback(self.interaction)

            self.interaction.edit_original_response.assert_called_once()
            args, kwargs = self.interaction.edit_original_response.call_args

            embed = kwargs.get("embed")
            self.assertIn("Test Quest", embed.title)

    @patch("cogs.quest_hub_cog.QuestSystem")
    async def test_quest_detail_view_accept_callback(self, MockQuestSystem):
        """Test QuestDetailView accepting a quest."""
        quests = [{"id": 1, "title": "Test Quest", "tier": "E", "summary": "A test"}]

        view = self.QuestDetailView(self.db, quest_id=1, quests_list=quests, interaction_user=self.user)

        qs_instance = MockQuestSystem.return_value
        qs_instance.accept_quest.return_value = True
        qs_instance.get_available_quests.return_value = []

        # We need to patch the next View it tries to instantiate
        with patch("cogs.quest_hub_cog.QuestBoardView", autospec=True) as MockBoardView:
            await view.accept_quest_callback(self.interaction)

            # Since back_to_quest_board_callback edies original response
            self.interaction.edit_original_response.assert_called_once()
            args, kwargs = self.interaction.edit_original_response.call_args
            embed = kwargs.get("embed")

            self.assertIn("Contract sealed", embed.fields[0]["value"])


if __name__ == "__main__":
    unittest.main()
