import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add repo root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock dependencies before import
if "pymongo" not in sys.modules:
    sys.modules["pymongo"] = MagicMock()
    sys.modules["pymongo.errors"] = MagicMock()

if "discord" not in sys.modules:
    sys.modules["discord"] = MagicMock()
if "discord.ext.tasks" not in sys.modules:
    sys.modules["discord.ext.tasks"] = MagicMock()
if "discord.ext.commands" not in sys.modules:
    sys.modules["discord.ext.commands"] = MagicMock()

# Setup the module mock properly to prevent ImportError
mock_discord = MagicMock()
mock_ext = MagicMock()
mock_commands = MagicMock()
mock_tasks = MagicMock()

# Explicitly mock commands.Cog to avoid StopIteration
class MockCog:
    pass
mock_commands.Cog = MockCog

# We need a custom mock for tasks.loop because it's used as a decorator
def mock_loop(*args, **kwargs):
    def decorator(func):
        func.start = MagicMock()
        func.cancel = MagicMock()
        func.before_loop = MagicMock()
        return func
    return decorator
mock_tasks.loop = mock_loop
mock_ext.tasks = mock_tasks
mock_ext.commands = mock_commands
mock_discord.ext = mock_ext

sys.modules["discord"] = mock_discord
sys.modules["discord.ext"] = mock_ext
sys.modules["discord.ext.commands"] = mock_commands
sys.modules["discord.ext.tasks"] = mock_tasks

# Import after mocking
import cogs.adventure_loop
from cogs.adventure_loop import AdventureLoop

class TestAdventureLoopRegression(unittest.TestCase):
    def setUp(self):
        self.mock_bot = MagicMock()

        # Patch DatabaseManager and Engine initialization within the cog
        patcher_db = patch("cogs.adventure_loop.DatabaseManager")
        patcher_engine = patch("cogs.adventure_loop.AdventureResolutionEngine")

        self.MockDB = patcher_db.start()
        self.MockEngine = patcher_engine.start()

        self.addCleanup(patcher_db.stop)
        self.addCleanup(patcher_engine.stop)

        self.mock_db = self.MockDB.return_value
        self.mock_engine = self.MockEngine.return_value

        # Create cog
        self.cog = AdventureLoop(self.mock_bot)

    @patch("cogs.adventure_loop.WorldTime")
    def test_worker_fetches_and_resolves_due_sessions(self, mock_world_time):
        """
        Regression Test: AdventureLoop Scheduler Execution
        - Verifies that the scheduler properly queries the database for due sessions.
        - Verifies that it passes fetched sessions to the resolution engine.
        """
        mock_now = MagicMock()
        mock_now.isoformat.return_value = "2023-01-01T12:00:00"
        mock_world_time.now.return_value = mock_now

        # Mock database returning 2 due sessions
        due_sessions = [
            {"discord_id": 1, "status": "in_progress"},
            {"discord_id": 2, "status": "in_progress"}
        ]
        self.mock_db.get_adventures_ending_before.return_value = due_sessions

        # Execute synchronous step (this is what the loop runs)
        self.cog._sync_worker_step()

        # Verify WorldTime usage
        mock_world_time.now.assert_called_once()

        # Verify DB fetch using correct ISO format
        self.mock_db.get_adventures_ending_before.assert_called_once_with("2023-01-01T12:00:00")

        # Verify Resolution Engine was called with the batch
        self.mock_engine.resolve_sessions_batch.assert_called_once_with(due_sessions)

    @patch("cogs.adventure_loop.WorldTime")
    def test_worker_handles_empty_sessions(self, mock_world_time):
        """
        Regression Test: Empty DB State
        - Verifies that empty result from DB does not crash or call the engine.
        """
        mock_world_time.now.return_value.isoformat.return_value = "2023-01-01T12:00:00"

        # DB returns empty list
        self.mock_db.get_adventures_ending_before.return_value = []

        # Execute
        self.cog._sync_worker_step()

        # Verify Engine NOT called
        self.mock_engine.resolve_sessions_batch.assert_not_called()

    @patch("cogs.adventure_loop.logger")
    @patch("cogs.adventure_loop.WorldTime")
    def test_worker_catches_engine_exceptions(self, mock_world_time, mock_logger):
        """
        Regression Test: Fault Tolerance
        - If resolve_sessions_batch raises an exception, the loop should log it and NOT crash.
        """
        mock_world_time.now.return_value.isoformat.return_value = "2023-01-01T12:00:00"
        self.mock_db.get_adventures_ending_before.return_value = [{"discord_id": 1}]

        # Make engine throw an exception
        self.mock_engine.resolve_sessions_batch.side_effect = Exception("Database Timeout")

        # Execute
        try:
            self.cog._sync_worker_step()
        except Exception as e:
            self.fail(f"_sync_worker_step raised an exception instead of catching it: {e}")

        # Verify logger caught it
        mock_logger.error.assert_called_once()
        self.assertIn("Failed batch resolution", mock_logger.error.call_args[0][0])

if __name__ == "__main__":
    unittest.main()
