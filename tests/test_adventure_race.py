# ruff: noqa: I001
import asyncio
import os
import sys
import unittest
import importlib
from unittest.mock import AsyncMock, MagicMock

# Add repo root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock Dependencies
sys.modules["pymongo"] = MagicMock()
sys.modules["pymongo.errors"] = MagicMock()

# Unconditionally mock discord to ensure isolation
mock_discord = MagicMock()
mock_discord.ButtonStyle.success = "success"
mock_discord.ButtonStyle.danger = "danger"
mock_discord.ButtonStyle.secondary = "secondary"
mock_discord.ButtonStyle.primary = "primary"

# Create dummy classes for mocking that allow inheritance and behavior verification
class MockView:
    def __init__(self, timeout=None):
        self.children = []
        self.timeout = timeout
    def add_item(self, item):
        self.children.append(item)

class MockButton:
    def __init__(self, label=None, style=None, emoji=None, row=None, custom_id=None):
        self.label = label
        self.style = style
        self.emoji = emoji
        self.row = row
        self.custom_id = custom_id
        self.disabled = False
        self.callback = None

    def _is_v2(self):
        return False

# Setup sys.modules
sys.modules["discord"] = mock_discord
sys.modules["discord.ui"] = MagicMock()
sys.modules["discord.ui"].View = MockView
sys.modules["discord.ui"].Button = MockButton
sys.modules["discord.ui"].Item = object  # Base class for items if needed

# Now import the code under test
# We need to ensure we can import from game_systems
from database.database_manager import DatabaseManager  # noqa: E402
from game_systems.adventure.adventure_manager import AdventureManager  # noqa: E402
import game_systems.adventure.ui.exploration_view  # noqa: E402
from game_systems.adventure.ui.exploration_view import ExplorationView  # noqa: E402
from game_systems.player.player_stats import PlayerStats  # noqa: E402

# FORCE RELOAD to ensure ExplorationView inherits from our MockView, not real View or previous mock
importlib.reload(game_systems.adventure.ui.exploration_view)
from game_systems.adventure.ui.exploration_view import ExplorationView  # noqa: E402, F811


class TestExplorationViewRace(unittest.IsolatedAsyncioTestCase):
    async def test_race_condition_double_click(self):
        # Setup mocks
        mock_db = MagicMock(spec=DatabaseManager)
        mock_manager = MagicMock(spec=AdventureManager)
        mock_user = MagicMock()
        mock_user.id = 12345

        # Mock player stats
        mock_stats = MagicMock(spec=PlayerStats)
        mock_stats.max_hp = 100

        # Mock interactions
        interaction1 = MagicMock()
        interaction1.user = mock_user
        interaction1.response = AsyncMock()
        interaction1.edit_original_response = AsyncMock()

        interaction2 = MagicMock()
        interaction2.user = mock_user
        interaction2.response = AsyncMock()
        interaction2.edit_original_response = AsyncMock()

        # Create view
        view = ExplorationView(
            db=mock_db,
            manager=mock_manager,
            location_id="test_loc",
            log=[],
            interaction_user=mock_user,
            player_stats=mock_stats,
            vitals={"current_hp": 100, "current_mp": 100},
            active_monster=None
        )

        # Verify inheritance from MockView (sanity check)
        # self.assertIsInstance(view, MockView)
        # Note: isinstance might fail if classes are reloaded weirdly, but behavior is what matters.

        # Mock simulate_adventure_step to be slow
        async def slow_simulation(*args, **kwargs):
            await asyncio.sleep(0.1)
            return {
                "sequence": [["You step forward."]],
                "dead": False,
                "vitals": {"current_hp": 100, "current_mp": 100},
                "player_stats": None,
                "active_monster": None
            }

        # Patch side_effect with delay
        def _original_side_effect(*args, **kwargs):
            return {
                "sequence": [["You step forward."]],
                "dead": False,
                "vitals": {"current_hp": 100, "current_mp": 100},
                "player_stats": None,
                "active_monster": None
            }

        def delayed_side_effect(*args, **kwargs):
            import time
            time.sleep(0.1)  # Sync sleep to block the thread
            return _original_side_effect(*args, **kwargs)

        mock_manager.simulate_adventure_step.side_effect = delayed_side_effect

        # We need to mock interaction.response.defer to yield control
        async def slow_defer():
            await asyncio.sleep(0.05)

        interaction1.response.defer.side_effect = slow_defer
        interaction2.response.defer.side_effect = slow_defer

        # Execute two callbacks concurrently
        task1 = asyncio.create_task(view.explore_callback(interaction1))
        task2 = asyncio.create_task(view.explore_callback(interaction2))

        await asyncio.gather(task1, task2)

        # Verification
        # If fixed, call_count should be 1. If broken, it's 2.
        print(f"Call count: {mock_manager.simulate_adventure_step.call_count}")

        # Assertion: Should be 1
        self.assertEqual(mock_manager.simulate_adventure_step.call_count, 1, "Simulation called more than once! Race condition detected.")

if __name__ == '__main__':
    unittest.main()
