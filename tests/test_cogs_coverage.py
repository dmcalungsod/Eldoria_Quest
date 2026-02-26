import unittest
from unittest.mock import AsyncMock, MagicMock, PropertyMock, patch

from cogs.chronicle_cog import ChronicleCog, TitleSelect
from cogs.faction_cog import FactionCog


class TestCogsCoverage(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.bot = MagicMock()
        self.mock_db = MagicMock()
        self.mock_interaction = MagicMock()
        self.mock_interaction.response.defer = AsyncMock()
        self.mock_interaction.followup.send = AsyncMock()
        self.mock_interaction.response.send_message = AsyncMock()
        self.mock_interaction.user.id = 12345

    async def test_chronicle_cog_command(self):
        with patch('cogs.chronicle_cog.DatabaseManager', return_value=self.mock_db):
            cog = ChronicleCog(self.bot)

            # Player exists
            self.mock_db.player_exists.return_value = True
            self.mock_db.get_titles.return_value = ["Title1"]
            self.mock_db.get_active_title.return_value = "Title1"

            await cog.chronicles.callback(cog, self.mock_interaction)

            self.mock_interaction.followup.send.assert_called_once()
            args = self.mock_interaction.followup.send.call_args
            self.assertIn("Active Title", args.kwargs['embed'].fields[0].name)

    async def test_chronicle_cog_no_player(self):
        with patch('cogs.chronicle_cog.DatabaseManager', return_value=self.mock_db):
            cog = ChronicleCog(self.bot)
            self.mock_db.player_exists.return_value = False

            await cog.chronicles.callback(cog, self.mock_interaction)

            args = self.mock_interaction.followup.send.call_args[0]
            self.assertIn("You do not have a character profile", args[0])

    async def test_title_select_callback(self):
        select = TitleSelect(["Title1"], "Title1")

        with patch.object(TitleSelect, 'values', new_callable=PropertyMock) as mock_values:
            mock_values.return_value = ["Title1"]

            # select.view cannot be set, but callback doesn't use it.

            with patch('cogs.chronicle_cog.DatabaseManager', return_value=self.mock_db):
                self.mock_db.set_active_title.return_value = True
                await select.callback(self.mock_interaction)

                self.mock_db.set_active_title.assert_called_with(12345, "Title1")
                self.mock_interaction.followup.send.assert_called()

    async def test_faction_cog_list(self):
        with patch('cogs.faction_cog.DatabaseManager', return_value=self.mock_db):
            cog = FactionCog(self.bot)

            with patch('cogs.faction_cog.FACTIONS', {"fac1": {"name": "Fac1", "emoji": "F", "description": "D", "favored_locations": ["loc1"]}}):
                with patch('cogs.faction_cog.LOCATIONS', {"loc1": {"name": "Loc1"}}):
                    await cog.list_factions.callback(cog, self.mock_interaction)

            self.mock_interaction.response.send_message.assert_called_once()

    async def test_faction_cog_join(self):
        with patch('cogs.faction_cog.DatabaseManager', return_value=self.mock_db):
            with patch('cogs.faction_cog.FactionSystem') as MockFS:
                cog = FactionCog(self.bot)
                MockFS.return_value.join_faction.return_value = (True, "Joined")

                choice = MagicMock()
                choice.value = "fac1"

                await cog.join_faction.callback(cog, self.mock_interaction, choice)

                self.mock_interaction.response.send_message.assert_called_with("Joined", ephemeral=True)

    async def test_faction_cog_status(self):
        with patch('cogs.faction_cog.DatabaseManager', return_value=self.mock_db):
            with patch('cogs.faction_cog.FactionSystem') as MockFS:
                cog = FactionCog(self.bot)

                # Case 1: No Faction
                MockFS.return_value.get_player_faction.return_value = None
                await cog.faction_status.callback(cog, self.mock_interaction)
                self.mock_interaction.response.send_message.assert_called_with(
                    "You are not in a faction. Use `/faction list` to see options.", ephemeral=True
                )

                # Case 2: In Faction
                MockFS.return_value.get_player_faction.return_value = {
                    "name": "Fac1", "emoji": "F", "description": "D",
                    "rank_title": "R", "rank_tier": 1, "reputation": 100
                }
                self.mock_interaction.response.send_message.reset_mock()
                await cog.faction_status.callback(cog, self.mock_interaction)

                self.mock_interaction.response.send_message.assert_called_once()
                args = self.mock_interaction.response.send_message.call_args
                self.assertEqual(args.kwargs['embed'].title, "F Fac1")

    async def test_faction_cog_leave(self):
        with patch('cogs.faction_cog.DatabaseManager', return_value=self.mock_db):
            with patch('cogs.faction_cog.FactionSystem') as MockFS:
                cog = FactionCog(self.bot)
                MockFS.return_value.leave_faction.return_value = (True, "Left")

                await cog.leave_faction.callback(cog, self.mock_interaction)

                self.mock_interaction.response.send_message.assert_called_with("Left", ephemeral=True)
