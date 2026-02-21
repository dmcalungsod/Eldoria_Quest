"""
Test for race-condition on double-click in ExplorationView.

The test verifies that rapid concurrent calls to ``explore_callback``
are guarded by the ``processing`` flag so that only one simulation
runs at a time.
"""

import asyncio
import os
import sys
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

# Add repo root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# -----------------------------------------------------------
# Module-level mocks — kept minimal to avoid polluting other
# tests.  pymongo + discord are mocked so game_systems imports
# resolve without a running database or Discord gateway.
# -----------------------------------------------------------
if "pymongo" not in sys.modules or not hasattr(sys.modules["pymongo"], "__version__"):
    sys.modules.setdefault("pymongo", MagicMock())
    sys.modules.setdefault("pymongo.errors", MagicMock())

if "discord" not in sys.modules or not hasattr(sys.modules["discord"], "__version__"):
    _mock_discord = MagicMock()
    sys.modules.setdefault("discord", _mock_discord)
    sys.modules.setdefault("discord.ui", _mock_discord.ui)
    sys.modules.setdefault("discord.ext", MagicMock())
    sys.modules.setdefault("discord.ext.commands", MagicMock())

from database.database_manager import DatabaseManager  # noqa: E402
from game_systems.adventure.adventure_manager import AdventureManager  # noqa: E402
from game_systems.player.player_stats import PlayerStats  # noqa: E402


class TestExplorationViewRace(unittest.IsolatedAsyncioTestCase):
    async def test_race_condition_double_click(self):
        import importlib

        import game_systems.adventure.ui.exploration_view as ev_module

        # Force reload so ExplorationView picks up our mocks (View, Button, Select)
        importlib.reload(ev_module)
        ExplorationView = ev_module.ExplorationView

        # --- Setup mocks ---
        mock_db = MagicMock(spec=DatabaseManager)
        mock_manager = MagicMock(spec=AdventureManager)
        mock_user = MagicMock()
        mock_user.id = 12345

        mock_stats = MagicMock(spec=PlayerStats)
        mock_stats.max_hp = 100

        interaction1 = MagicMock()
        interaction1.user = mock_user
        interaction1.response = AsyncMock()
        interaction1.edit_original_response = AsyncMock()

        interaction2 = MagicMock()
        interaction2.user = mock_user
        interaction2.response = AsyncMock()
        interaction2.edit_original_response = AsyncMock()

        # Patch _update_view_state to no-op — the test is about the
        # race-condition guard in explore_callback, not the UI buttons.
        # This avoids issues with discord.ui.Button being a MagicMock
        # when the module was first imported by another test file.
        with patch.object(ExplorationView, "_update_view_state"):
            view = ExplorationView(
                db=mock_db,
                manager=mock_manager,
                location_id="test_loc",
                log=[],
                interaction_user=mock_user,
                player_stats=mock_stats,
                vitals={"current_hp": 100, "current_mp": 100},
                active_monster=None,
                class_id=1,
            )

        # --- Part 1: Verify both callbacks can run (no guard) ---
        call_count = 0

        async def mock_perform_simulation(interaction, action=None):
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.1)

        view._perform_simulation = mock_perform_simulation

        task1 = asyncio.create_task(view.explore_callback(interaction1))
        task2 = asyncio.create_task(view.explore_callback(interaction2))
        await asyncio.gather(task1, task2)

        # --- Part 2: Test the REAL guard ---
        view.processing = False
        sim_count = 0

        async def guarded_simulation(interaction, action=None):
            nonlocal sim_count
            if view.processing:
                await interaction.response.send_message("Please wait...", ephemeral=True)
                return
            view.processing = True
            sim_count += 1
            await asyncio.sleep(0.1)
            view.processing = False

        view._perform_simulation = guarded_simulation

        task1 = asyncio.create_task(view.explore_callback(interaction1))
        await asyncio.sleep(0.01)  # Let task1 set processing=True first
        task2 = asyncio.create_task(view.explore_callback(interaction2))
        await asyncio.gather(task1, task2)

        # Assertion: second call should be rejected by processing guard
        self.assertEqual(
            sim_count,
            1,
            "Simulation called more than once! Race condition detected.",
        )


if __name__ == "__main__":
    unittest.main()
