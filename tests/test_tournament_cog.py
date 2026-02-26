import datetime
import importlib
import os
import sys
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

# Ensure root dir is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestTournamentCog(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        # Patch sys.modules to mock dependencies BEFORE importing the unit under test
        self.modules_patcher = patch.dict(sys.modules)
        self.modules_patcher.start()

        # Mock discord
        mock_discord = MagicMock()
        mock_discord.app_commands = MagicMock()

        # Mock app_commands.command decorator
        def command_decorator(*args, **kwargs):
            def decorator(func):
                return func
            return decorator
        mock_discord.app_commands.command = MagicMock(side_effect=command_decorator)

        # Mock checks.has_permissions decorator
        def checks_decorator(*args, **kwargs):
            def decorator(func):
                return func
            return decorator
        mock_discord.app_commands.checks = MagicMock()
        mock_discord.app_commands.checks.has_permissions = MagicMock(side_effect=checks_decorator)

        # Mock app_commands.describe decorator
        def describe_decorator(*args, **kwargs):
            def decorator(func):
                return func
            return decorator
        mock_discord.app_commands.describe = MagicMock(side_effect=describe_decorator)

        # Mock discord.Embed to capture init args
        class MockEmbed:
            def __init__(self, **kwargs):
                self.title = kwargs.get('title')
                self.description = kwargs.get('description')
                self.color = kwargs.get('color')
                self.fields = []
            def add_field(self, name, value, inline=True):
                self.fields.append(MagicMock(name=name, value=value, inline=inline))
            def set_footer(self, text):
                self.footer = text
        mock_discord.Embed = MockEmbed

        # Create a dummy Cog class to avoid MagicMock inheritance issues
        class DummyCog:
            pass

        mock_discord.ext.commands = MagicMock()
        mock_discord.ext.commands.Cog = DummyCog
        mock_discord.ext.tasks = MagicMock()

        # Mock loop decorator
        def loop_decorator(*args, **kwargs):
            def decorator(func):
                mock_task = MagicMock()
                mock_task.start = MagicMock()
                mock_task.cancel = MagicMock()

                def before_loop_decorator(f):
                    return f
                mock_task.before_loop = before_loop_decorator
                mock_task.callback = func
                return mock_task
            return decorator

        mock_loop = MagicMock(side_effect=loop_decorator)
        mock_discord.ext.tasks.loop = mock_loop

        sys.modules["discord"] = mock_discord
        sys.modules["discord.app_commands"] = mock_discord.app_commands
        sys.modules["discord.ext"] = mock_discord.ext
        sys.modules["discord.ext.commands"] = mock_discord.ext.commands
        sys.modules["discord.ext.tasks"] = mock_discord.ext.tasks

        # Mock DatabaseManager dependencies
        mock_pymongo = MagicMock()
        sys.modules["pymongo"] = mock_pymongo
        sys.modules["pymongo.errors"] = MagicMock()

        # Import modules locally to avoid E402 and ensure mocks are used
        import cogs.tournament_cog
        importlib.reload(cogs.tournament_cog)

        self.TournamentCog = cogs.tournament_cog.TournamentCog

        # Setup Bot Mock
        self.bot = MagicMock()
        self.bot.guilds = []

        # Setup DB Mock
        self.mock_db_cls = MagicMock()
        with patch("cogs.tournament_cog.DatabaseManager", return_value=self.mock_db_cls) as mock_db_cls:
            self.mock_db_instance = mock_db_cls.return_value
            self.cog = self.TournamentCog(self.bot)

        # Mock System
        self.cog.system = MagicMock()

    def tearDown(self):
        self.modules_patcher.stop()

    async def test_init_starts_loop(self):
        # Verify start() was called on the loop task
        # self.cog.check_tournament_cycle should be the mock task
        self.cog.check_tournament_cycle.start.assert_called_once()

    async def test_tournament_status_no_active(self):
        interaction = AsyncMock()
        self.cog.db.get_active_tournament.return_value = None

        await self.cog.tournament_status(interaction)

        interaction.response.send_message.assert_called_once()
        args, kwargs = interaction.response.send_message.call_args
        embed = kwargs.get('embed')
        self.assertIn("No Active Tournament", embed.title)

    async def test_tournament_status_active(self):
        interaction = AsyncMock()
        interaction.user.id = 123

        future = (datetime.datetime.now() + datetime.timedelta(days=2)).isoformat()
        self.cog.db.get_active_tournament.return_value = {
            "id": 1,
            "type": "monster_kills",
            "end_time": future
        }
        self.cog.db.get_player_tournament_score.return_value = 50

        await self.cog.tournament_status(interaction)

        interaction.response.send_message.assert_called_once()
        args, kwargs = interaction.response.send_message.call_args
        embed = kwargs.get('embed')
        self.assertIn("Active Tournament", embed.title)
        # Check fields. Our MockEmbed stores fields as objects with .value
        self.assertIn("50 pts", embed.fields[1].value)

    async def test_leaderboard_no_active(self):
        interaction = AsyncMock()
        self.cog.system.get_leaderboard.return_value = (None, [])

        await self.cog.tournament_leaderboard(interaction)

        interaction.response.send_message.assert_called_once()
        args = interaction.response.send_message.call_args[0]
        self.assertIn("No tournament is currently active", args[0])

    async def test_leaderboard_active(self):
        interaction = AsyncMock()
        active = {"id": 1, "type": "monster_kills"}
        leaders = [
            {"rank": 1, "name": "Player1", "score": 100},
            {"rank": 2, "name": "Player2", "score": 90}
        ]
        self.cog.system.get_leaderboard.return_value = (active, leaders)

        await self.cog.tournament_leaderboard(interaction)

        interaction.response.send_message.assert_called_once()
        args, kwargs = interaction.response.send_message.call_args
        embed = kwargs.get('embed')
        self.assertIn("Leaderboard", embed.title)
        self.assertIn("Player1", embed.description)

    async def test_admin_start(self):
        interaction = AsyncMock()
        # Mock checks? No, we call the function directly.

        self.cog.system.TOURNAMENT_TYPES = ["monster_kills"]
        self.cog.db.create_tournament.return_value = 101

        await self.cog.admin_start(interaction, "monster_kills")

        self.cog.system.end_current_tournament.assert_called_once()
        self.cog.db.create_tournament.assert_called_once()
        interaction.response.send_message.assert_called_once()
        self.assertIn("Started Tournament #101", interaction.response.send_message.call_args[0][0])

    async def test_admin_start_invalid(self):
        interaction = AsyncMock()
        self.cog.system.TOURNAMENT_TYPES = ["monster_kills"]

        await self.cog.admin_start(interaction, "invalid_type")

        self.cog.db.create_tournament.assert_not_called()
        interaction.response.send_message.assert_called_once()
        self.assertIn("Invalid type", interaction.response.send_message.call_args[0][0])

    async def test_admin_end(self):
        interaction = AsyncMock()
        self.cog.system.end_current_tournament.return_value = "Ended."

        await self.cog.admin_end(interaction)

        self.cog.system.end_current_tournament.assert_called_once()
        interaction.response.send_message.assert_called_once()

    async def test_check_tournament_cycle_ends_expired(self):
        # Setup
        past = (datetime.datetime.now() - datetime.timedelta(hours=1)).isoformat()
        self.cog.db.get_active_tournament.return_value = {
            "id": 1,
            "type": "monster_kills",
            "end_time": past
        }
        self.cog.system.end_current_tournament.return_value = "Tournament Ended."

        # Execute the original function (callback)
        # self.cog.check_tournament_cycle is the mock task object
        await self.cog.check_tournament_cycle.callback(self.cog)

        # Verify
        self.cog.system.end_current_tournament.assert_called_once()

    async def test_check_tournament_cycle_starts_new(self):
        # Setup: No active tournament, and it's Monday
        self.cog.db.get_active_tournament.side_effect = [None, {"id": 2, "type": "monster_kills"}]

        # Mock WorldTime.now to return a Monday
        with patch("game_systems.core.world_time.WorldTime.now") as mock_now:
            mock_date = datetime.datetime(2023, 10, 23, 12, 0, 0) # Oct 23 2023 is a Monday
            mock_now.return_value = mock_date

            self.cog.system.start_weekly_tournament.return_value = 2

            await self.cog.check_tournament_cycle.callback(self.cog)

            self.cog.system.start_weekly_tournament.assert_called_once()


if __name__ == "__main__":
    unittest.main()
