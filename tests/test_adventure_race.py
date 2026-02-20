
import asyncio
import sys
import unittest
import importlib
from unittest.mock import AsyncMock, MagicMock

# 1. Force Clean Slate
if "discord" in sys.modules:
    del sys.modules["discord"]
if "discord.ui" in sys.modules:
    del sys.modules["discord.ui"]

# 2. Create fresh mocks
mock_discord = MagicMock()
sys.modules["discord"] = mock_discord
sys.modules["discord.ui"] = MagicMock()

# Define mock classes explicitly (don't inherit from Mock/Item to avoid pollution)
class MockView:
    def __init__(self, timeout=None):
        self.children = []
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

sys.modules["discord.ui"].View = MockView
sys.modules["discord.ui"].Button = MockButton
discord = mock_discord

# Now import the code under test
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.database_manager import DatabaseManager
from game_systems.adventure.adventure_manager import AdventureManager
import game_systems.adventure.ui.exploration_view
# FORCE RELOAD to pick up the MockButton class
importlib.reload(game_systems.adventure.ui.exploration_view)
from game_systems.adventure.ui.exploration_view import ExplorationView
from game_systems.player.player_stats import PlayerStats


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

        # Mock simulate_adventure_step to be slow
        # We need to make sure the side_effect is thread-safe or simply use a delay.

        # We will wrap the manager method to include a delay
        # Just use a return_value first to ensure structure is correct
        base_return = {
                "sequence": [["You step forward."]],
                "dead": False,
                "vitals": {"current_hp": 100, "current_mp": 100},
                "player_stats": None,
                "active_monster": None
        }

        def delayed_side_effect(*args, **kwargs):
            import time
            time.sleep(0.1) # Sync sleep to block the thread
            return base_return

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
