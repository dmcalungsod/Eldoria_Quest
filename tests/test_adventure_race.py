
import asyncio
import os
import sys
import unittest
from unittest.mock import AsyncMock, MagicMock

# Add repo root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock Dependencies
sys.modules["pymongo"] = MagicMock()
sys.modules["pymongo.errors"] = MagicMock()

# Mock discord if not available
try:
    import discord
    from discord.ui import Button, View
    Item = discord.ui.Item
    if not isinstance(Item, type):
        raise ImportError("discord.ui.Item is not a type (likely mocked)")
except (ImportError, AttributeError):
    # Create dummy classes for mocking
    mock_discord = MagicMock()
    sys.modules["discord"] = mock_discord
    sys.modules["discord.ui"] = MagicMock()

    Item = object

    # Mock Button and View specifically to allow inheritance
    class View:
        def __init__(self, timeout=None):
            self.children = []
        def add_item(self, item):
            self.children.append(item)
        def clear_items(self):
            self.children.clear()

    class Button(Item):
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

    sys.modules["discord.ui"].View = View
    sys.modules["discord.ui"].Button = Button
    discord = mock_discord

# Now import the code under test
# We need to ensure we can import from game_systems
from database.database_manager import DatabaseManager  # noqa: E402
from game_systems.adventure.adventure_manager import AdventureManager  # noqa: E402
from game_systems.player.player_stats import PlayerStats  # noqa: E402


class TestExplorationViewRace(unittest.IsolatedAsyncioTestCase):
    async def test_race_condition_double_click(self):
        # Import here to avoid conflict with other tests mocking discord
        from game_systems.adventure.ui.exploration_view import ExplorationView

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
        # We need to mock _setup_buttons calling _get_button_state
        # Or just let it run if mocks are sufficient

        view = ExplorationView(
            db=mock_db,
            manager=mock_manager,
            location_id="test_loc",
            log=[],
            interaction_user=mock_user,
            player_stats=mock_stats,
            vitals={"current_hp": 100, "current_mp": 100},
            active_monster=None,
            class_id=1
        )

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

        # Patch asyncio.to_thread to run our slow simulation
        # Because the view calls asyncio.to_thread(self.manager.simulate_adventure_step, ...)

        # We also need to patch asyncio.sleep inside explore_callback so the animation loop doesn't take forever
        # But we WANT the simulation to be slow to prove the race.

        # The view uses asyncio.to_thread. In test environment, this runs in a thread.
        # We can just mock manager.simulate_adventure_step, but since it's called via to_thread,
        # we need to make sure the side_effect is thread-safe or simply use a delay.

        mock_manager.simulate_adventure_step.side_effect = lambda *args: {
                "sequence": [["You step forward."]],
                "dead": False,
                "vitals": {"current_hp": 100, "current_mp": 100},
                "player_stats": None,
                "active_monster": None
        }

        # To ensure the race condition, we need the first call to pause AFTER checking any lock (if present)
        # and BEFORE the operation completes.

        # We will wrap the manager method to include a delay
        original_side_effect = mock_manager.simulate_adventure_step.side_effect
        def delayed_side_effect(*args, **kwargs):
            import time
            time.sleep(0.1) # Sync sleep to block the thread
            return original_side_effect(*args, **kwargs)

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
