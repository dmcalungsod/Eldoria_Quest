import asyncio
import datetime
import os
import sys
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

# Add repo root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# Define a pass-through mock for tasks.loop
def mock_loop(*args, **kwargs):
    def decorator(func):
        func.start = MagicMock()
        func.cancel = MagicMock()
        func.before_loop = MagicMock()
        return func

    return decorator


class TestEventScheduling(unittest.TestCase):
    def setUp(self):
        # 1. Start a patcher for sys.modules to isolate our mocks
        self.modules_patcher = patch.dict(sys.modules)
        self.modules_patcher.start()
        self.addCleanup(self.modules_patcher.stop)

        # 2. Setup Mocks
        mock_discord = MagicMock()
        mock_discord.ext.commands.Cog = object
        mock_discord.ext.tasks.loop = mock_loop

        sys.modules["discord"] = mock_discord
        sys.modules["discord.ext"] = mock_discord.ext
        sys.modules["discord.ext.commands"] = mock_discord.ext.commands
        sys.modules["discord.app_commands"] = MagicMock()

        mock_db_module = MagicMock()
        sys.modules["database.database_manager"] = mock_db_module

        # Mock game_systems as a package with submodules
        mock_gs = MagicMock()
        sys.modules["game_systems"] = mock_gs

        # Ensure submodules can be imported
        mock_gs.data = MagicMock()
        mock_gs.data.emojis = MagicMock()
        sys.modules["game_systems.data"] = mock_gs.data
        sys.modules["game_systems.data.emojis"] = mock_gs.data.emojis

        mock_wt_module = MagicMock()
        sys.modules["game_systems.world_time"] = mock_wt_module

        mock_wes_module = MagicMock()
        sys.modules["game_systems.events.world_event_system"] = mock_wes_module

        # Set attributes on the mocks
        mock_wes_module.WorldEventSystem.MYSTIC_MERCHANT = "mystic_merchant"
        mock_wes_module.WorldEventSystem.HARVEST_FESTIVAL = "harvest_festival"

        # 3. Import cogs.event_cog inside the patched environment
        # We must ensure it's not already cached from real imports (handled by patch.dict, sort of)
        # But if it was already imported by another test, patch.dict might copy it.
        # We want to force reload it to pick up OUR mocks.
        if "cogs.event_cog" in sys.modules:
            del sys.modules["cogs.event_cog"]

        import cogs.event_cog

        self.EventCog = cogs.event_cog.EventCog

        # 4. Initialize Cog
        self.bot = MagicMock()
        self.cog = self.EventCog(self.bot)

        # 5. Setup instance mocks
        self.cog.system = MagicMock()
        self.cog.db = MagicMock()
        self.cog._announce = AsyncMock()

        self.cog.system.EVENT_CONFIGS = {
            "mystic_merchant": {"name": "The Mystic Merchant", "description": "Test Description"}
        }

    @patch("game_systems.world_time.WorldTime")
    @patch("random.random")
    def test_mystic_merchant_starts_on_roll(self, mock_random, mock_world_time):
        # 1. Setup
        self.cog.system.get_current_event.return_value = None
        mock_world_time.now.return_value = datetime.datetime(2023, 1, 1, 12, 0, 0)
        mock_random.return_value = 0.01
        self.cog.system.start_event.return_value = True

        # 2. Run
        asyncio.run(self.cog.check_event_cycle())

        # 3. Verify
        self.cog.system.start_event.assert_called_with("mystic_merchant", 24)
        self.cog._announce.assert_called()
        args, _ = self.cog._announce.call_args
        self.assertIn("Mystic", args[0])

    @patch("game_systems.world_time.WorldTime")
    @patch("random.random")
    def test_mystic_merchant_does_not_start_on_fail(self, mock_random, mock_world_time):
        self.cog.system.get_current_event.return_value = None
        mock_world_time.now.return_value = datetime.datetime(2023, 1, 1, 12, 0, 0)
        mock_random.return_value = 0.5

        asyncio.run(self.cog.check_event_cycle())

        self.cog.system.start_event.assert_not_called()

    @patch("game_systems.world_time.WorldTime")
    @patch("random.random")
    def test_no_event_start_if_active(self, mock_random, mock_world_time):
        self.cog.system.get_current_event.return_value = {"type": "blood_moon"}

        asyncio.run(self.cog.check_event_cycle())

        self.cog.system.start_event.assert_not_called()


if __name__ == "__main__":
    unittest.main()
