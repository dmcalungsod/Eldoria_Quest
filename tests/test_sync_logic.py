import asyncio
import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch

# Ensure test file path allows correct imports
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT_DIR)

# Mock environment variables BEFORE import
os.environ["DISCORD_BOT_TOKEN"] = "mock_token"
os.environ["GUILD_ID"] = "123456789"

# --- MOCKING SETUP ---
# We must setup mocks carefully so imports work as expected.

# 1. discord
discord_mock = MagicMock()
sys.modules["discord"] = discord_mock

# 2. discord.ext
ext_mock = MagicMock()
sys.modules["discord.ext"] = ext_mock

# 3. discord.ext.commands
commands_mock = MagicMock()
sys.modules["discord.ext.commands"] = commands_mock
ext_mock.commands = commands_mock  # crucial for 'from discord.ext import commands'

# 4. Other modules
sys.modules["aiohttp"] = MagicMock()
sys.modules["aiohttp.web"] = MagicMock()
sys.modules["dotenv"] = MagicMock()
sys.modules["database.create_database"] = MagicMock()
sys.modules["database.populate_database"] = MagicMock()

# Setup discord mocks
discord_mock.Intents = MagicMock()
discord_mock.Intents.default = MagicMock(return_value=MagicMock())
discord_mock.Game = MagicMock()
discord_mock.Object = MagicMock()
discord_mock.HTTPException = Exception
discord_mock.LoginFailure = Exception

# Setup MockBotBase
class MockBotBase:
    def __init__(self, *args, **kwargs):
        self.tree = MagicMock()
        self.tree.sync = AsyncMock()
        self.tree.copy_global_to = MagicMock()
        self.tree.clear_commands = MagicMock()
        self.user = MagicMock()
        self.user.id = 123
        self.load_extension = AsyncMock()
        # Mock tree.sync to track calls
        # self.tree.sync is already AsyncMock, which records calls.

commands_mock.Bot = MockBotBase

# Now import main
import main  # noqa: E402

async def _test_sync_logic_async():
    print("Testing sync logic...")

    # 1. Test with GUILD_ID set (simulated dev environment)
    print("\n--- Test Case 1: GUILD_ID is set ---")

    main.GUILD_ID = "123456789"

    bot = main.EldoriaBot()
    # Confirm bot is instance of EldoriaBot (and not a Mock)
    print(f"Bot type: {type(bot)}")

    with patch("main.start_health_server", new_callable=AsyncMock) as mock_health:
        await bot.setup_hook()

    print("Calls to tree.sync:", bot.tree.sync.call_args_list)

    guild_sync_called = False
    global_sync_called = False

    for call in bot.tree.sync.call_args_list:
        args, kwargs = call
        if 'guild' in kwargs or (args and args[0]):
             guild_sync_called = True
        else:
            global_sync_called = True

    if guild_sync_called:
        print("PASS: Guild sync called.")
    else:
        print("FAIL: Guild sync NOT called.")

    if global_sync_called:
        print("PASS: Global sync called.")
    else:
        print("FAIL: Global sync NOT called.")

    # 2. Test without GUILD_ID
    print("\n--- Test Case 2: GUILD_ID is NOT set ---")
    main.GUILD_ID = None

    bot = main.EldoriaBot()

    with patch("main.start_health_server", new_callable=AsyncMock) as mock_health:
        await bot.setup_hook()

    print("Calls to tree.sync:", bot.tree.sync.call_args_list)

    global_sync_called = False
    for call in bot.tree.sync.call_args_list:
        args, kwargs = call
        if not kwargs and not args:
            global_sync_called = True

    if global_sync_called:
        print("PASS: Global sync called.")
    else:
        print("FAIL: Global sync NOT called.")

def test_sync_logic():
    """Wrapper to run async test logic in pytest environment without plugins."""
    asyncio.run(_test_sync_logic_async())

if __name__ == "__main__":
    test_sync_logic()
