import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add root to sys.path
sys.path.append(os.getcwd())

class TestAdventureLoop(unittest.TestCase):
    def setUp(self):
        # Patch sys.modules to mock discord and pymongo safely within the test scope
        self.modules_patcher = patch.dict(sys.modules)
        self.modules_patcher.start()

        if "pymongo" not in sys.modules or not hasattr(sys.modules["pymongo"], "__version__"):
            sys.modules.setdefault("pymongo", MagicMock())
            sys.modules.setdefault("pymongo.errors", MagicMock())

        class DummyLoopDecorator:
            def __init__(self, *args, **kwargs):
                pass
            def __call__(self, func):
                func.start = MagicMock()
                func.cancel = MagicMock()
                func.before_loop = lambda f: f
                return func

        class DummyTasks:
            loop = DummyLoopDecorator

        class DummyCommands:
            class Cog:
                pass

        class DummyExt:
            commands = DummyCommands
            tasks = DummyTasks

        class DummyDiscord:
            ext = DummyExt

        if "discord" not in sys.modules or not hasattr(sys.modules["discord"], "__version__"):
            sys.modules["discord"] = DummyDiscord()
            sys.modules["discord.ext"] = DummyExt()
            sys.modules["discord.ext.commands"] = DummyCommands()
            sys.modules["discord.ext.tasks"] = DummyTasks()

        if isinstance(sys.modules["discord"].ext, MagicMock):
            sys.modules["discord.ext.tasks"].loop = DummyLoopDecorator

        # Import locally to avoid global pollution
        from cogs.adventure_loop import AdventureLoop
        self.AdventureLoop = AdventureLoop

    def tearDown(self):
        self.modules_patcher.stop()

    @patch("cogs.adventure_loop.WorldTime")
    @patch("cogs.adventure_loop.DatabaseManager")
    @patch("cogs.adventure_loop.AdventureResolutionEngine")
    def test_sync_worker_step_with_sessions(self, mock_engine_cls, mock_db_cls, mock_time):
        mock_bot = MagicMock()
        mock_db = mock_db_cls.return_value
        mock_engine = mock_engine_cls.return_value

        mock_time.now.return_value.isoformat.return_value = "2026-02-28T12:00:00"
        due_sessions = [{"discord_id": 1, "duration_minutes": 60}]
        mock_db.get_adventures_ending_before.return_value = due_sessions

        loop_cog = self.AdventureLoop(mock_bot)
        loop_cog.adventure_worker = MagicMock()
        loop_cog._sync_worker_step()

        mock_time.now.assert_called()
        mock_db.get_adventures_ending_before.assert_called_once_with("2026-02-28T12:00:00")
        mock_engine.resolve_sessions_batch.assert_called_once_with(due_sessions)

    @patch("cogs.adventure_loop.WorldTime")
    @patch("cogs.adventure_loop.DatabaseManager")
    @patch("cogs.adventure_loop.AdventureResolutionEngine")
    def test_sync_worker_step_no_sessions(self, mock_engine_cls, mock_db_cls, mock_time):
        mock_bot = MagicMock()
        mock_db = mock_db_cls.return_value
        mock_engine = mock_engine_cls.return_value

        mock_time.now.return_value.isoformat.return_value = "2026-02-28T12:00:00"
        mock_db.get_adventures_ending_before.return_value = []

        loop_cog = self.AdventureLoop(mock_bot)
        loop_cog.adventure_worker = MagicMock()
        loop_cog._sync_worker_step()

        mock_engine.resolve_sessions_batch.assert_not_called()

    @patch("cogs.adventure_loop.DatabaseManager")
    @patch("cogs.adventure_loop.AdventureResolutionEngine")
    def test_cog_unload(self, mock_engine_cls, mock_db_cls):
        mock_bot = MagicMock()
        loop_cog = self.AdventureLoop(mock_bot)
        loop_cog.adventure_worker = MagicMock()

        loop_cog.cog_unload()
        loop_cog.adventure_worker.cancel.assert_called_once()

    @patch("cogs.adventure_loop.WorldTime")
    @patch("cogs.adventure_loop.DatabaseManager")
    @patch("cogs.adventure_loop.AdventureResolutionEngine")
    def test_sync_worker_step_exception_handling(self, mock_engine_cls, mock_db_cls, mock_time):
        mock_bot = MagicMock()
        mock_db = mock_db_cls.return_value
        mock_engine = mock_engine_cls.return_value

        mock_time.now.return_value.isoformat.return_value = "2026-02-28T12:00:00"
        due_sessions = [{"discord_id": 1, "duration_minutes": 60}]
        mock_db.get_adventures_ending_before.return_value = due_sessions
        mock_engine.resolve_sessions_batch.side_effect = Exception("Test Database Failure")

        loop_cog = self.AdventureLoop(mock_bot)
        loop_cog.adventure_worker = MagicMock()
        try:
            loop_cog._sync_worker_step()
        except Exception:
            self.fail("_sync_worker_step raised Exception unexpectedly!")

        mock_engine.resolve_sessions_batch.assert_called_once_with(due_sessions)

if __name__ == "__main__":
    unittest.main()
