import asyncio
import os
import sys
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

# Add repo root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestExplorationViewRace(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        # 1. Setup Mocks
        self.mock_discord = MagicMock()
        self.mock_discord.ButtonStyle.success = "success"
        self.mock_discord.ButtonStyle.danger = "danger"
        self.mock_discord.ButtonStyle.secondary = "secondary"
        self.mock_discord.ButtonStyle.primary = "primary"
        self.mock_discord.Color.dark_red.return_value = "dark_red"
        self.mock_discord.Color.dark_green.return_value = "dark_green"
        self.mock_discord.Color.dark_grey.return_value = "dark_grey"

        # Capture Real Item if available
        RealItem = object
        if "discord.ui" in sys.modules:
            try:
                candidate = sys.modules["discord.ui"].Item
                if isinstance(candidate, type):
                    RealItem = candidate
            except AttributeError:
                pass

        class MockView:
            def __init__(self, timeout=180):
                self.children = []
            def add_item(self, item):
                self.children.append(item)
            def clear_items(self):
                self.children.clear()

        class MockButton(RealItem):
            def __init__(self, label=None, style=None, custom_id=None, emoji=None, row=None, disabled=False):
                self.callback = None
                self.label = label
                self.disabled = disabled
            def _is_v2(self):
                return False

        class MockSelect(RealItem):
            def __init__(self, placeholder=None, min_values=1, max_values=1, row=None, disabled=False, options=None, custom_id=None):
                self.callback = None
                self.options = options or []
                self.disabled = disabled
                self.custom_id = custom_id

        self.mock_discord.ui.View = MockView
        self.mock_discord.ui.Button = MockButton
        self.mock_discord.ui.Select = MockSelect
        self.mock_discord.SelectOption = MagicMock()

        # 2. Patch modules
        self.modules_patcher = patch.dict(sys.modules, {
            "discord": self.mock_discord,
            "discord.ui": self.mock_discord.ui,
            "pymongo": MagicMock(),
            "pymongo.errors": MagicMock(),
            "cogs.ui_helpers": MagicMock(),
            "game_systems.adventure.ui.adventure_embeds": MagicMock(),
        })
        self.modules_patcher.start()

        # 3. Import/Reload module
        if "game_systems.adventure.ui.exploration_view" in sys.modules:
            del sys.modules["game_systems.adventure.ui.exploration_view"]
        import game_systems.adventure.ui.exploration_view
        self.ExplorationView = game_systems.adventure.ui.exploration_view.ExplorationView

        from game_systems.player.player_stats import PlayerStats
        self.PlayerStats = PlayerStats

    def tearDown(self):
        self.modules_patcher.stop()

    async def test_race_condition_double_click(self):
        # Setup mocks
        mock_db = MagicMock()
        mock_manager = MagicMock()
        mock_user = MagicMock()
        mock_user.id = 12345

        # Mock player stats
        mock_stats = MagicMock(spec=self.PlayerStats)
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

        view = self.ExplorationView(
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

        # Mock simulate_adventure_step to be slow using time.sleep
        # This will block the thread worker
        def slow_simulation(*args, **kwargs):
            import time
            time.sleep(0.2)
            return {
                "sequence": [["You step forward."]],
                "dead": False,
                "vitals": {"current_hp": 100, "current_mp": 100},
                "player_stats": None,
                "active_monster": None,
            }

        mock_manager.simulate_adventure_step.side_effect = slow_simulation

        # We need to ensure interaction.response.defer yields control back to event loop
        # so second task can start before first task finishes the threaded work
        async def async_defer():
            await asyncio.sleep(0.01) # Small yielding delay

        interaction1.response.defer.side_effect = async_defer
        interaction2.response.defer.side_effect = async_defer

        # Execute two callbacks concurrently
        task1 = asyncio.create_task(view.explore_callback(interaction1))

        # Ensure task1 starts and hits the await defer
        await asyncio.sleep(0.02)

        task2 = asyncio.create_task(view.explore_callback(interaction2))

        await asyncio.gather(task1, task2)

        # Verification
        # If fixed (processing flag works), call_count should be 1.
        print(f"Call count: {mock_manager.simulate_adventure_step.call_count}")

        self.assertEqual(
            mock_manager.simulate_adventure_step.call_count,
            1,
            "Simulation called more than once! Race condition detected.",
        )

        # Verify second interaction got "Please wait"
        interaction2.response.send_message.assert_called_with("Please wait...", ephemeral=True)


if __name__ == "__main__":
    unittest.main()
