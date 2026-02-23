import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add repo root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock external dependencies before importing AdventureManager
# This prevents ImportErrors or side effects from unmocked modules
if "pymongo" not in sys.modules:
    sys.modules["pymongo"] = MagicMock()
    sys.modules["pymongo.errors"] = MagicMock()

if "discord" not in sys.modules:
    sys.modules["discord"] = MagicMock()

from game_systems.adventure.adventure_manager import AdventureManager
from database.database_manager import DatabaseManager


class TestAdventureDeathPenalty(unittest.TestCase):
    def setUp(self):
        self.mock_db = MagicMock(spec=DatabaseManager)
        self.mock_bot = MagicMock()

        # Patch InventoryManager since it's instantiated in AdventureManager.__init__
        with patch(
            "game_systems.adventure.adventure_manager.InventoryManager"
        ) as MockInventoryManager:
            self.manager = AdventureManager(self.mock_db, self.mock_bot)
            self.mock_inventory_manager = MockInventoryManager.return_value
            # Ensure the manager instance uses our mock inventory manager
            self.manager.inventory_manager = self.mock_inventory_manager

    @patch("game_systems.adventure.adventure_manager.AdventureSession")
    def test_death_penalty_calculation(self, MockAdventureSession):
        """
        Regression Test: Verify death penalty logic (Aurum loss, Material loss).
        - Aurum: 10% of CURRENT (banked) Aurum is lost.
        - Materials: 50% of GATHERED (session) materials are lost.
        - Session Rewards: XP and Aurum collected IN SESSION are completely lost.
        """
        discord_id = 12345

        # 1. Setup Mock DB Data
        # Active session exists
        self.mock_db.get_combat_context_bundle.return_value = {
            "active_session": {
                "location_id": "forest_outskirts",
                "start_time": "2023-01-01T00:00:00",
                "duration_minutes": 60,
            }
        }

        # Player has 1000 Aurum banked
        self.mock_db.get_player_field.side_effect = lambda uid, field: (
            1000 if field == "aurum" else 1
        )

        # Mock PlayerStats (needed for _grant_rewards_internal call inside _handle_death_rewards)
        self.mock_db.get_player_stats_json.return_value = {
            "strength": 10,
            "endurance": 10,
            "dexterity": 10,
            "agility": 10,
            "magic": 10,
            "luck": 10,
        }

        # Mock get_player for reward calculation
        self.mock_db.get_player.return_value = {
            "level": 5,
            "experience": 1000,
            "exp_to_next": 2000,
            "current_hp": 0,
            "current_mp": 50,
            "vestige_pool": 0,
        }

        # 2. Setup Mock Session
        mock_session_instance = MockAdventureSession.return_value
        mock_session_instance.discord_id = discord_id

        # Loot collected during adventure (The "Session Loot")
        # These are raw counts before penalty
        mock_session_instance.loot = {
            "exp": 500,  # Should be lost completely
            "aurum": 200,  # Should be lost completely
            "iron_ore": 10,  # Material: 50% kept -> 5
            "potion": 4,  # Material/Consumable: 50% kept -> 2
            "rare_gem": 1,  # Material: 50% of 1 is 0.5 -> int(0.5) = 0 kept (Total loss)
        }

        # Simulate step returns DEAD
        mock_session_instance.simulate_step.return_value = {
            "dead": True,
            "sequence": [["You died."]],
        }

        # 3. Execute
        result = self.manager.simulate_adventure_step(discord_id)

        # 4. Verifications

        # A. Verify Aurum Penalty (10% of 1000 banked Aurum)
        # deduct_aurum should be called with 100
        self.mock_db.deduct_aurum.assert_called_with(discord_id, 100)

        # B. Verify Session Loot (XP/Aurum) is removed from session.loot
        # The code pops "exp" and "aurum" from the loot dict directly
        self.assertNotIn("exp", mock_session_instance.loot)
        self.assertNotIn("aurum", mock_session_instance.loot)

        # C. Verify Material Penalty (50% kept)
        # inventory_manager.add_items_bulk is called with the items to KEEP
        call_args = self.manager.inventory_manager.add_items_bulk.call_args
        self.assertIsNotNone(
            call_args, "InventoryManager.add_items_bulk was not called!"
        )

        added_items = call_args[0][1]  # Second arg is the list of items
        item_map = {item["item_key"]: item["amount"] for item in added_items}

        self.assertEqual(item_map.get("iron_ore"), 5, "Should keep 50% of 10 Iron Ore")
        self.assertEqual(item_map.get("potion"), 2, "Should keep 50% of 4 Potions")
        self.assertIsNone(
            item_map.get("rare_gem"), "Should lose 1 Rare Gem (50% of 1 = 0)"
        )

        # D. Verify Session End
        self.mock_db.end_adventure_session.assert_called_with(discord_id)

        # E. Verify Result Structure
        self.assertTrue(result["dead"])

        # F. Verify Loss Message in Sequence
        # The last frame should contain the loss report
        last_frame = result["sequence"][-1]
        loss_text = "\n".join(last_frame)
        self.assertIn("Losses Incurred", loss_text)
        self.assertIn("-100", loss_text)  # Aurum loss
        self.assertIn("-5x Iron Ore", loss_text)  # 5 lost
        self.assertIn(
            "-2x", loss_text
        )  # 2 potions lost (name might vary if not in MATERIALS)
        # Note: "potion" is not in MATERIALS, so it uses "potion" as name.
        # "rare_gem" is not in MATERIALS, so it uses "rare_gem" as name.
        self.assertIn("-1x rare_gem", loss_text)  # 1 lost


if __name__ == "__main__":
    unittest.main()
