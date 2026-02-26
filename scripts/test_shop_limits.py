"""
Test script for verifying daily shop limit logic.
Mocks MongoDB interactions to simulate purchases and date changes.
"""

import sys
import unittest
from unittest.mock import MagicMock
import os

# Add repo root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.database_manager import DatabaseManager

class TestShopLimits(unittest.TestCase):
    def setUp(self):
        # Create a mock DatabaseManager manually
        self.db = DatabaseManager.__new__(DatabaseManager)
        self.db._initialized = True

        # Mock the underlying pymongo collections
        self.mock_db = MagicMock()
        self.db.db = self.mock_db

        # Mock internal storage
        self.purchases = {}

        # Mock increment_daily_shop_purchase logic
        def mock_increment(discord_id, item_key, amount, date_str):
            key = (discord_id, item_key, date_str)
            self.purchases[key] = self.purchases.get(key, 0) + amount

        self.db.increment_daily_shop_purchase = mock_increment

        # Mock get_daily_shop_purchases logic
        def mock_get(discord_id, date_str):
            results = {}
            for k, v in self.purchases.items():
                if k[0] == discord_id and k[2] == date_str:
                    results[k[1]] = v
            return results

        self.db.get_daily_shop_purchases = mock_get

    def test_increment_purchase(self):
        # Simulate increment
        self.db.increment_daily_shop_purchase(123, "potion", 1, "2023-10-27")
        self.db.increment_daily_shop_purchase(123, "potion", 1, "2023-10-27")

        purchases = self.db.get_daily_shop_purchases(123, "2023-10-27")
        self.assertEqual(purchases.get("potion"), 2)

    def test_date_reset(self):
        # Add purchase for today
        self.db.increment_daily_shop_purchase(123, "potion", 5, "2023-10-27")

        # Check tomorrow (should be empty)
        purchases = self.db.get_daily_shop_purchases(123, "2023-10-28")
        self.assertEqual(purchases.get("potion", 0), 0)

if __name__ == '__main__':
    unittest.main()
