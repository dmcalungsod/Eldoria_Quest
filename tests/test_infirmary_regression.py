import os
import sys
import unittest
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio

# Add repo root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock external dependencies before importing DatabaseManager
if "pymongo" not in sys.modules:
    sys.modules["pymongo"] = MagicMock()
    sys.modules["pymongo.errors"] = MagicMock()

# Instead of blindly overriding discord, we try to use the real discord if available
# or minimally mock it so View works
try:
    import discord
    from discord.ui import View
    has_discord = True
except ImportError:
    has_discord = False
    mock_discord = MagicMock()
    mock_discord.ui = MagicMock()

    class MockView:
        def __init__(self, timeout=None):
            pass
        def add_item(self, item):
            pass

    mock_discord.ui.View = MockView
    mock_discord.ui.Button = MagicMock
    mock_discord.ui.Select = MagicMock
    sys.modules["discord"] = mock_discord
    sys.modules["discord.ui"] = mock_discord.ui
    sys.modules["discord.ext"] = MagicMock()
    sys.modules["discord.ext.commands"] = MagicMock()


from database.database_manager import DatabaseManager

class TestInfirmaryRegression(unittest.TestCase):
    def test_beginner_free_healing_regression(self):
        """
        Regression Test: Beginners (Level 3 or below) get free healing.
        Prevents death loop for low-level players.
        """
        # Level 1 player missing HP and MP
        cost = DatabaseManager.calculate_heal_cost(
            current_hp=10, current_mp=10, max_hp=100, max_mp=50, level=1
        )
        self.assertEqual(cost, 0, "Level 1 player should have free healing")

        # Level 3 player missing HP and MP
        cost = DatabaseManager.calculate_heal_cost(
            current_hp=10, current_mp=10, max_hp=100, max_mp=50, level=3
        )
        self.assertEqual(cost, 0, "Level 3 player should have free healing")

        # Level 4 player missing HP and MP
        cost = DatabaseManager.calculate_heal_cost(
            current_hp=10, current_mp=10, max_hp=100, max_mp=50, level=4
        )
        # Expected: (90 * 2) + (40 * 3) = 180 + 120 = 300
        self.assertEqual(cost, 300, "Level 4 player should pay for healing")

    def test_beginner_free_healing_full_health(self):
         # Level 1 player full HP and MP
        cost = DatabaseManager.calculate_heal_cost(
            current_hp=100, current_mp=50, max_hp=100, max_mp=50, level=1
        )
        self.assertEqual(cost, 0, "Level 1 player with full health should have free healing")

    @patch('cogs.utils.ui_helpers.get_player_or_error', new_callable=AsyncMock)
    @patch('asyncio.to_thread', new_callable=AsyncMock)
    def test_prevent_adventure_start_low_health(self, mock_to_thread, mock_get_player_or_error):
        """
        Regression Test: Prevent adventure start if HP < 15%.
        """
        if not has_discord:
            self.skipTest("Requires discord.py for UI views")

        from game_systems.adventure.ui.setup_view import AdventureSetupView

        mock_db = MagicMock()
        mock_manager = MagicMock()
        mock_interaction = MagicMock()
        mock_interaction.user.id = 123
        mock_interaction.response = AsyncMock()
        mock_interaction.followup = AsyncMock()

        mock_get_player_or_error.return_value = True

        # Set up a player with 10 HP / 100 Max HP (10% < 15%)
        mock_vitals = {"current_hp": 10}

        # We only need enough structure for PlayerStats.from_dict to work without error
        mock_stats_json = {
            "STR": {"base": 10},
            "END": {"base": 10},
            "DEX": {"base": 10},
            "AGI": {"base": 10},
            "MAG": {"base": 10},
            "LCK": {"base": 10},
            "HP": {"base": 100},
            "MP": {"base": 50}
        }

        def mock_to_thread_side_effect(*args, **kwargs):
            func = args[0]
            if func == mock_db.get_player_vitals:
                return mock_vitals
            elif func == mock_db.get_player_stats_json:
                return mock_stats_json
            return None

        mock_to_thread.side_effect = mock_to_thread_side_effect

        view = AdventureSetupView(mock_db, mock_manager, mock_interaction.user, "F", 1)

        asyncio.run(view.start_callback(mock_interaction))

        # Should not defer or call start_adventure
        mock_interaction.response.defer.assert_not_called()

        # Should send the warning message
        mock_interaction.response.send_message.assert_called_once()
        args, kwargs = mock_interaction.response.send_message.call_args
        self.assertIn("Your health is critically low", args[0])
        self.assertTrue(kwargs.get("ephemeral"))

    @patch('game_systems.adventure.adventure_manager.WorldTime')
    def test_retreat_emergency_extraction_penalty(self, mock_world_time):
        """
        Regression Test: "Emergency Extraction" penalty ONLY applies when retreating from active combat.
        If the adventure ends naturally (status = completed), no penalty is applied.
        """
        from game_systems.adventure.adventure_manager import AdventureManager

        mock_db = MagicMock()
        mock_bot = MagicMock()

        # We need to mock level for _grant_rewards_internal
        mock_db.get_player.return_value = {
            "level": 5,
            "experience": 1000,
            "exp_to_next": 2000,
            "current_hp": 100,
            "current_mp": 50,
        }
        mock_db.get_player_field.return_value = 5

        mock_db.get_player_stats_json.return_value = {
            "STR": {"base": 10},
            "END": {"base": 10},
            "DEX": {"base": 10},
            "AGI": {"base": 10},
            "MAG": {"base": 10},
            "LCK": {"base": 10},
            "HP": {"base": 100},
            "MP": {"base": 50}
        }

        # Patch InventoryManager since it's instantiated in AdventureManager.__init__
        with patch("game_systems.adventure.adventure_manager.InventoryManager") as MockInventoryManager:
            manager = AdventureManager(mock_db, mock_bot)
            mock_inventory_manager = MockInventoryManager.return_value
            manager.inventory_manager = mock_inventory_manager

        discord_id = 12345

        # Test Case 1: Naturally completed auto-retreat
        mock_db.get_active_adventure.return_value = {
            "discord_id": discord_id,
            "location_id": "forest",
            "loot_collected": '{"wood": 10, "stone": 5}',
            "active": 1,
            "logs": "[]",
            "active_monster_json": '{"name": "Dragon", "hp": 100}',
            "duration_minutes": 60,
            "start_time": "2023-01-01T00:00:00",
            "status": "completed" # Key detail: adventure is natively completed
        }
        mock_db.lock_adventure_for_claiming.return_value = True

        with patch(
            "game_systems.adventure.adventure_manager.MATERIALS",
            {"wood": {"name": "Wood"}, "stone": {"name": "Stone"}},
        ):
            summary = manager.end_adventure(discord_id)

            self.assertIsNotNone(summary)
            # No penalty logs should exist for naturally completed adventures
            self.assertEqual(len(summary["penalty_logs"]), 0)

            # Loot should NOT be penalized
            awarded_items = summary["loot"]
            wood_award = next(i for i in awarded_items if i["key"] == "wood")
            stone_award = next(i for i in awarded_items if i["key"] == "stone")

            self.assertEqual(wood_award["amount"], 10)
            self.assertEqual(stone_award["amount"], 5)

        # Test Case 2: Manual retreat (panic)
        mock_db.get_active_adventure.return_value = {
            "discord_id": discord_id,
            "location_id": "forest",
            "loot_collected": '{"wood": 10, "stone": 5}',
            "active": 1,
            "logs": "[]",
            "active_monster_json": '{"name": "Dragon", "hp": 100}',
            "duration_minutes": 60,
            "start_time": "2023-01-01T00:00:00",
            "status": "in_progress" # Still active when user clicked "Retreat"
        }
        mock_db.lock_adventure_for_claiming.return_value = True

        with patch(
            "game_systems.adventure.adventure_manager.MATERIALS",
            {"wood": {"name": "Wood"}, "stone": {"name": "Stone"}},
        ):
            summary = manager.end_adventure(discord_id)

            self.assertIsNotNone(summary)
            # Should have penalty log about panic
            self.assertTrue(len(summary["penalty_logs"]) > 0)
            self.assertIn("Emergency Extraction", summary["penalty_logs"][0])

            # Loot SHOULD be penalized (25% loss)
            awarded_items = summary["loot"]
            wood_award = next(i for i in awarded_items if i["key"] == "wood")
            stone_award = next(i for i in awarded_items if i["key"] == "stone")

            # Wood: 10 * 0.75 = 7.5 -> 7
            # Stone: 5 * 0.75 = 3.75 -> 3
            self.assertEqual(wood_award["amount"], 7)
            self.assertEqual(stone_award["amount"], 3)


if __name__ == "__main__":
    unittest.main()
