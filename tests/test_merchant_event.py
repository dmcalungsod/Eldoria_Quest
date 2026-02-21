import os
import sys
import unittest
from unittest.mock import MagicMock, patch

sys.path.append(os.getcwd())

class TestMerchantEvent(unittest.TestCase):
    def setUp(self):
        # Patch sys.modules to mock dependencies
        self.modules_patcher = patch.dict(sys.modules, {
            "pymongo": MagicMock(),
            "pymongo.errors": MagicMock(),
            "discord": MagicMock(),
            "discord.ext": MagicMock(),
            "discord.ui": MagicMock(),
            "discord.app_commands": MagicMock(),
        })
        self.modules_patcher.start()

        # Import modules under test inside the patched environment
        # We use importlib.import_module to ensure we get the module,
        # but if it was already imported, we might get the cached version.
        # However, since we are patching sys.modules, imports inside these modules
        # (like 'import pymongo') will use our mocks IF those modules are reloaded or imported for the first time.

        # To be safe, we import them here.
        # Note: We rely on the fact that these modules handle imports at top-level.
        try:
            import cogs.merchant_cog
            import database.database_manager
            import game_systems.events.world_event_system

            # Force reload if they were already imported to ensure they pick up the mocks?
            # Reloading might be risky if other tests depend on the original versions.
            # But since we are inside a test method (or setUp), effects should be limited?
            # Actually, reload modifies the module object in place. That persists after the test!
            # So DO NOT reload globally if you can avoid it.

            # BUT, if we don't reload, and they were already imported with REAL pymongo,
            # then our mocks in sys.modules won't affect the 'pymongo' symbol inside 'database_manager'.

            # However, for Unit Testing with mocks, we usually assume isolation.
            # The previous error was because we set sys.modules GLOBALLY at file level.
            # By moving it here, we only set it during this test class execution.

            self.db_module = database.database_manager
            self.wes_module = game_systems.events.world_event_system
            self.merchant_module = cogs.merchant_cog

        except ImportError:
            # If import fails (e.g. strict dependency checks), we fail
            raise

        # Setup Mock DB
        self.mock_db = MagicMock(spec=self.db_module.DatabaseManager)
        # Mock methods used
        self.mock_db.set_active_world_event = MagicMock()
        self.mock_db.get_active_world_event = MagicMock(return_value=None)
        self.mock_db.end_active_world_event = MagicMock()
        self.mock_db.purchase_item = MagicMock(return_value=(True, {"name": "Test Item"}, 100))

        # Initialize System
        self.event_system = self.wes_module.WorldEventSystem(self.mock_db)

    def tearDown(self):
        self.modules_patcher.stop()

    def test_start_merchant_event(self):
        # Use constants from the module
        MYSTIC_MERCHANT = self.wes_module.WorldEventSystem.MYSTIC_MERCHANT

        success = self.event_system.start_event(MYSTIC_MERCHANT, 1)
        self.assertTrue(success)

        self.mock_db.set_active_world_event.assert_called_once()
        args, _ = self.mock_db.set_active_world_event.call_args
        self.assertEqual(args[0], MYSTIC_MERCHANT)

    def test_merchant_event_config(self):
        MYSTIC_MERCHANT = self.wes_module.WorldEventSystem.MYSTIC_MERCHANT
        config = self.event_system.EVENT_CONFIGS.get(MYSTIC_MERCHANT)
        self.assertIsNotNone(config)
        self.assertEqual(config["name"], "The Void Trader")
        self.assertIn("luck_boost", config["modifiers"])

    def test_inventory_contains_items(self):
        inventory = self.merchant_module.MERCHANT_INVENTORY
        self.assertIn("elixir_luck", inventory)
        self.assertIn("void_heart", inventory)
        self.assertIn("mythic_amber", inventory)

if __name__ == "__main__":
    unittest.main()
