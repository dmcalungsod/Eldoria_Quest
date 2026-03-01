import sys
import unittest
from unittest.mock import MagicMock, patch

# Mock pymongo globally
sys.modules["pymongo"] = MagicMock()
sys.modules["pymongo.errors"] = MagicMock()

import cogs.adventure_loop
import importlib

class TestAdventureLoop(unittest.IsolatedAsyncioTestCase):
    @patch("cogs.adventure_loop.DatabaseManager")
    @patch("cogs.adventure_loop.AdventureResolutionEngine")
    def setUp(self, mock_engine_class, mock_db_class):
        self.mock_bot = MagicMock()

        self.mock_db = mock_db_class.return_value
        self.mock_engine = mock_engine_class.return_value

        is_polluted = isinstance(cogs.adventure_loop.AdventureLoop, MagicMock)
        if is_polluted:
            importlib.reload(cogs.adventure_loop)

        # To completely avoid test runner pollution and discord.ext module mock failures,
        # we mock the adventure_worker loop completely here so __init__ doesn't fail.
        self.patcher = patch("discord.ext.tasks.loop")
        self.mock_loop = self.patcher.start()

        # When tasks.loop is used as a decorator, it returns a function that expects the coro
        # and returns an object with start/cancel/etc.
        def loop_decorator(*args, **kwargs):
            def wrap(func):
                mock_task = MagicMock()
                mock_task.coro = func
                mock_task.start = MagicMock()
                mock_task.cancel = MagicMock()
                mock_task.before_loop = lambda f: f
                return mock_task
            return wrap

        self.mock_loop.side_effect = loop_decorator

        importlib.reload(cogs.adventure_loop)

        self.cog = cogs.adventure_loop.AdventureLoop(self.mock_bot)

        # Restore mocks for test verification
        self.cog.db = self.mock_db
        self.cog.engine = self.mock_engine

    def tearDown(self):
        self.patcher.stop()

    def test_init(self):
        """Test the initialization of the cog."""
        self.assertEqual(self.cog.bot, self.mock_bot)
        self.assertEqual(self.cog.db, self.mock_db)
        self.assertEqual(self.cog.engine, self.mock_engine)
        self.cog.adventure_worker.start.assert_called_once()

    @patch("cogs.adventure_loop.WorldTime")
    def test_sync_worker_step_no_sessions(self, mock_world_time):
        """Test worker step when there are no due sessions."""
        mock_world_time.now.return_value.isoformat.return_value = "2023-01-01T00:00:00"
        self.mock_db.get_adventures_ending_before.return_value = []

        self.cog._sync_worker_step()

        self.mock_db.get_adventures_ending_before.assert_called_once_with("2023-01-01T00:00:00")
        self.mock_engine.resolve_sessions_batch.assert_not_called()

    @patch("cogs.adventure_loop.WorldTime")
    def test_sync_worker_step_with_sessions(self, mock_world_time):
        """Test worker step when there are due sessions."""
        mock_world_time.now.return_value.isoformat.return_value = "2023-01-01T00:00:00"
        due_sessions = [{"_id": "session1"}, {"_id": "session2"}]
        self.mock_db.get_adventures_ending_before.return_value = due_sessions

        self.cog._sync_worker_step()

        self.mock_db.get_adventures_ending_before.assert_called_once_with("2023-01-01T00:00:00")
        self.mock_engine.resolve_sessions_batch.assert_called_once_with(due_sessions)

    @patch("cogs.adventure_loop.WorldTime")
    def test_sync_worker_step_exception(self, mock_world_time):
        """Test worker step handles exceptions gracefully."""
        mock_world_time.now.return_value.isoformat.return_value = "2023-01-01T00:00:00"
        due_sessions = [{"_id": "session1"}]
        self.mock_db.get_adventures_ending_before.return_value = due_sessions

        # Make the engine throw an exception
        self.mock_engine.resolve_sessions_batch.side_effect = Exception("Test Exception")

        try:
            self.cog._sync_worker_step()
        except Exception:
            self.fail("_sync_worker_step raised an exception instead of handling it")

        self.mock_engine.resolve_sessions_batch.assert_called_once_with(due_sessions)

if __name__ == "__main__":
    unittest.main()
