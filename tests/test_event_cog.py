import datetime
import os
import sys
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

# Add repo root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestEventCog(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.modules_patcher = patch.dict(sys.modules)
        self.modules_patcher.start()

        # Mock discord
        mock_discord = MagicMock()
        mock_discord.app_commands = MagicMock()

        # Mock decorators
        def pass_decorator(*args, **kwargs):
            def decorator(func):
                return func

            return decorator

        mock_discord.app_commands.command = MagicMock(side_effect=pass_decorator)
        mock_discord.app_commands.checks.has_permissions = MagicMock(
            side_effect=pass_decorator
        )
        mock_discord.app_commands.describe = MagicMock(side_effect=pass_decorator)

        # Mock Embed
        class MockEmbed:
            def __init__(self, **kwargs):
                self.title = kwargs.get("title")
                self.description = kwargs.get("description")
                self.fields = []

            def add_field(self, name, value, inline=True):
                m = MagicMock()
                m.name = name
                m.value = value
                self.fields.append(m)

        mock_discord.Embed = MockEmbed

        # Mock ext
        mock_ext = MagicMock()

        class DummyCog:
            pass

        mock_ext.commands.Cog = DummyCog

        # Mock tasks loop
        def loop_decorator(*args, **kwargs):
            def decorator(func):
                mock_task = MagicMock()
                mock_task.start = MagicMock()
                mock_task.cancel = MagicMock()
                mock_task.callback = func

                def before_loop_decorator(f):
                    return f

                mock_task.before_loop = before_loop_decorator
                return mock_task

            return decorator

        mock_ext.tasks.loop = MagicMock(side_effect=loop_decorator)

        sys.modules["discord"] = mock_discord
        sys.modules["discord.app_commands"] = mock_discord.app_commands
        sys.modules["discord.ext"] = mock_ext
        sys.modules["discord.ext.commands"] = mock_ext.commands
        sys.modules["discord.ext.tasks"] = mock_ext.tasks

        # Mock DatabaseManager
        mock_pymongo = MagicMock()
        sys.modules["pymongo"] = mock_pymongo
        sys.modules["pymongo.errors"] = MagicMock()

        # Import
        import cogs.event_cog

        importlib = __import__("importlib")
        importlib.reload(cogs.event_cog)

        self.EventCog = cogs.event_cog.EventCog
        self.WorldEventSystem = cogs.event_cog.WorldEventSystem

        self.bot = AsyncMock()
        self.bot.guilds = []

        # Mock DB and System
        self.mock_db_cls = MagicMock()
        with patch(
            "cogs.event_cog.DatabaseManager", return_value=self.mock_db_cls
        ) as mock_db_cls:
            self.mock_db = mock_db_cls.return_value
            self.cog = self.EventCog(self.bot)

        # Mock System inside Cog
        self.cog.system = MagicMock()
        # Ensure system has constants
        self.cog.system.HARVEST_FESTIVAL = "harvest_festival"
        self.cog.system.MYSTIC_MERCHANT = "mystic_merchant"
        self.cog.system.EVENT_CONFIGS = {
            "harvest_festival": {"name": "Harvest Festival", "description": "Desc"},
            "mystic_merchant": {"name": "Mystic Merchant", "description": "Desc"},
            "blood_moon": {"name": "Blood Moon", "description": "Desc"},
        }

    def tearDown(self):
        self.modules_patcher.stop()

    async def test_event_status_no_active(self):
        interaction = AsyncMock()
        self.cog.system.get_current_event.return_value = None

        await self.cog.event_status(interaction)

        interaction.response.send_message.assert_called_once()
        kwargs = interaction.response.send_message.call_args.kwargs
        self.assertIn("No Active Event", kwargs["embed"].title)

    async def test_event_status_active(self):
        interaction = AsyncMock()
        future = (datetime.datetime.now() + datetime.timedelta(days=1)).isoformat()

        active = {
            "name": "Blood Moon",
            "description": "Scary",
            "end_time": future,
            "modifiers": {"exp": 2.0},
        }
        self.cog.system.get_current_event.return_value = active

        await self.cog.event_status(interaction)

        interaction.response.send_message.assert_called_once()
        kwargs = interaction.response.send_message.call_args.kwargs
        self.assertIn("Blood Moon", kwargs["embed"].title)
        # Check modifiers
        fields = kwargs["embed"].fields
        self.assertTrue(any("Global Effects" in f.name for f in fields))

    async def test_admin_start_success(self):
        interaction = AsyncMock()
        self.cog.system.start_event.return_value = True

        await self.cog.admin_start(interaction, "blood_moon", 24)

        self.cog.system.start_event.assert_called_with("blood_moon", 24)
        interaction.response.send_message.assert_called_once()
        self.assertIn(
            "Started Event", interaction.response.send_message.call_args[0][0]
        )

    async def test_admin_start_invalid(self):
        interaction = AsyncMock()

        await self.cog.admin_start(interaction, "invalid_event", 24)

        self.cog.system.start_event.assert_not_called()
        interaction.response.send_message.assert_called_once()
        self.assertIn("Invalid type", interaction.response.send_message.call_args[0][0])

    async def test_admin_end(self):
        interaction = AsyncMock()

        await self.cog.admin_end(interaction)

        self.cog.system.end_current_event.assert_called_once()
        interaction.response.send_message.assert_called_once()

    async def test_check_event_cycle_harvest_festival(self):
        # Setup: No active event, Date is Oct 1st, 12:00
        self.cog.system.get_current_event.return_value = None

        mock_date = datetime.datetime(2023, 10, 1, 12, 0, 0)
        with patch(
            "game_systems.core.world_time.WorldTime.now", return_value=mock_date
        ):
            self.cog.system.start_event.return_value = True

            await self.cog.check_event_cycle.callback(self.cog)

            self.cog.system.start_event.assert_called_with("harvest_festival", 24 * 7)

    async def test_check_event_cycle_mystic_merchant(self):
        # Setup: No active event, Not Harvest Festival
        self.cog.system.get_current_event.return_value = None

        mock_date = datetime.datetime(2023, 5, 1, 12, 0, 0)
        with patch(
            "game_systems.core.world_time.WorldTime.now", return_value=mock_date
        ):
            # First call for time_quake (0.5 > 0.02 fails), second call for mystic_merchant (0.01 < 0.02 succeeds)
            with patch("random.random", side_effect=[0.5, 0.01]):
                self.cog.system.start_event.return_value = True

                await self.cog.check_event_cycle.callback(self.cog)

                self.cog.system.start_event.assert_called_with("mystic_merchant", 24)

    async def test_announce(self):
        # Create a mock guild and channel
        guild = MagicMock()
        guild.name = "TestGuild"
        channel = AsyncMock()
        channel.name = "guild-hall"
        guild.text_channels = [channel]

        self.bot.guilds = [guild]

        # Mock discord.utils.get to return our channel
        # discord.utils.get(iterable, **attrs)
        # We can implement a simple side effect or just return the channel
        def utils_get(iterable, **kwargs):
            # Return the first item that matches kwargs
            for item in iterable:
                match = True
                for k, v in kwargs.items():
                    if getattr(item, k, None) != v:
                        match = False
                        break
                if match:
                    return item
            return None

        with patch("discord.utils.get", side_effect=utils_get):
            # Test private method _announce
            await self.cog._announce("Hello World")

        channel.send.assert_called_with("Hello World")

    async def test_check_event_cycle_builders_boon(self):
        """Verify Builder's Boon auto-starts on random chance."""
        self.cog.system.get_current_event.return_value = None
        self.cog.system.start_event.return_value = True

        self.cog.system.EVENT_CONFIGS = {
            "builders_boon": {"name": "The Builder's Boon", "description": "Test"}
        }

        with patch(
            "game_systems.core.world_time.WorldTime.now",
            return_value=datetime.datetime(2023, 2, 1, 12, 0, 0),
        ):
            with patch("random.random", side_effect=[0.5, 0.5, 0.01]):
                with patch.object(self.cog, "_announce", AsyncMock()):
                    await self.cog.check_event_cycle.callback(self.cog)

        self.cog.system.start_event.assert_called_once_with("builders_boon", 48)


if __name__ == "__main__":
    unittest.main()
