import os
import sys
import unittest
from unittest.mock import MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock pymongo
sys.modules["pymongo"] = MagicMock()
sys.modules["pymongo.errors"] = MagicMock()


# Mock View
class MockView:
    def __init__(self, timeout=None):
        pass

    def add_item(self, item):
        pass


# Mock Discord
mock_discord = MagicMock()
sys.modules["discord"] = mock_discord
sys.modules["discord.ext"] = MagicMock()

# Mock discord.ui correctly
mock_ui = MagicMock()
mock_ui.View = MockView
sys.modules["discord.ui"] = mock_ui
mock_discord.ui = mock_ui


from game_systems.data.shop_data import SHOP_INVENTORY  # noqa: E402

# Force reload to ensure ShopView uses the MockView defined above
# We delete from sys.modules to handle cases where it might be mocked
if "cogs.shop_cog" in sys.modules:
    del sys.modules["cogs.shop_cog"]

from cogs.shop_cog import ShopView  # noqa: E402


class TestShopViewIntegration(unittest.TestCase):
    def test_shop_view_calls_purchase_item_success(self):
        mock_db = MagicMock()
        mock_user = MagicMock()
        mock_user.id = 12345
        current_aurum = 1000

        view = ShopView(mock_db, mock_user, current_aurum)

        item_key = "hp_potion_1"
        price = SHOP_INVENTORY[item_key]  # 40

        # Mock purchase_item return: (success, item_data, new_balance)
        mock_db.purchase_item.return_value = (True, {"name": "Test Potion"}, 960)

        success, result, new_aurum = view._execute_purchase(item_key)

        # Verify call
        mock_db.purchase_item.assert_called_once()
        args, _ = mock_db.purchase_item.call_args
        self.assertEqual(args[0], 12345)
        self.assertEqual(args[1], item_key)
        self.assertEqual(args[3], price)

        self.assertTrue(success)
        self.assertEqual(new_aurum, 960)

    def test_shop_view_handles_insufficient_funds(self):
        mock_db = MagicMock()
        mock_user = MagicMock()
        mock_user.id = 12345
        current_aurum = 10

        view = ShopView(mock_db, mock_user, current_aurum)

        item_key = "hp_potion_1"
        price = SHOP_INVENTORY[item_key]  # 40

        # Mock purchase_item return: (failure, msg, 0)
        mock_db.purchase_item.return_value = (False, "Insufficient Aurum.", 0)

        success, result, new_aurum = view._execute_purchase(item_key)

        mock_db.purchase_item.assert_called_once()
        self.assertFalse(success)
        self.assertEqual(result, "Insufficient Aurum.")
        self.assertEqual(new_aurum, 0)

    def test_shop_view_with_custom_inventory(self):
        mock_db = MagicMock()
        mock_user = MagicMock()
        mock_user.id = 12345
        current_aurum = 1000

        # Custom inventory with modified price for an existing item
        custom_inv = {"hp_potion_1": 999}

        view = ShopView(mock_db, mock_user, current_aurum, inventory=custom_inv)

        item_key = "hp_potion_1"
        price = custom_inv[item_key]  # 999

        # Mock purchase_item return
        mock_db.purchase_item.return_value = (True, {"name": "Dewfall Tonic"}, 1)

        success, result, new_aurum = view._execute_purchase(item_key)

        # Verify call used the custom price
        mock_db.purchase_item.assert_called_once()
        args, _ = mock_db.purchase_item.call_args
        self.assertEqual(args[3], price)


if __name__ == "__main__":
    unittest.main()
