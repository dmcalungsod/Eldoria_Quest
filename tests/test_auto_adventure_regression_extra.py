import sys
import unittest
from unittest.mock import MagicMock, patch

sys.modules["pymongo"] = MagicMock()
sys.modules["pymongo.errors"] = MagicMock()

class FakeCommandsCog:
    pass

class FakeCommands:
    Cog = FakeCommandsCog

def fake_loop(**kw):
    def decorator(func):
        func.start = MagicMock()
        func.cancel = MagicMock()
        func.before_loop = lambda f: f
        return func
    return decorator

class FakeTasks:
    loop = fake_loop

class FakeExt:
    commands = FakeCommands
    tasks = FakeTasks

class FakeDiscord:
    ext = FakeExt

sys.modules["discord"] = FakeDiscord()
sys.modules["discord.ext"] = FakeExt()
sys.modules["discord.ext.commands"] = FakeCommands()
sys.modules["discord.ext.tasks"] = FakeTasks()

import cogs.adventure_loop

class TestAutoAdventureLoop(unittest.TestCase):
    @patch('cogs.adventure_loop.DatabaseManager')
    @patch('cogs.adventure_loop.AdventureResolutionEngine')
    def test_sync_worker_step(self, MockEngine, MockDB):
        cog = cogs.adventure_loop.AdventureLoop(MagicMock())
        with patch('cogs.adventure_loop.WorldTime') as mock_time:
            mock_time.now.return_value.isoformat.return_value = "2023-01-01T00:00:00"
            cog.db.get_adventures_ending_before.return_value = [
                {"discord_id": 1, "location_id": "forest"}
            ]

            cog._sync_worker_step()

            mock_time.now.return_value.isoformat.assert_called_once()
            cog.db.get_adventures_ending_before.assert_called_once_with("2023-01-01T00:00:00")
            cog.engine.resolve_sessions_batch.assert_called_once_with(
                [{"discord_id": 1, "location_id": "forest"}]
            )

    @patch('cogs.adventure_loop.DatabaseManager')
    @patch('cogs.adventure_loop.AdventureResolutionEngine')
    def test_sync_worker_step_empty(self, MockEngine, MockDB):
        cog = cogs.adventure_loop.AdventureLoop(MagicMock())
        with patch('cogs.adventure_loop.WorldTime') as mock_time:
            mock_time.now.return_value.isoformat.return_value = "2023-01-01T00:00:00"
            cog.db.get_adventures_ending_before.return_value = []

            cog._sync_worker_step()

            mock_time.now.return_value.isoformat.assert_called_once()
            cog.db.get_adventures_ending_before.assert_called_once_with("2023-01-01T00:00:00")
            cog.engine.resolve_sessions_batch.assert_not_called()

if __name__ == "__main__":
    unittest.main()
