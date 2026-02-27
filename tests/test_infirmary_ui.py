import importlib
import os
import sys
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

# Add repo root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Helper Mocks
class MockView:
    def __init__(self, timeout=None):
        self.children = []
        self.timeout = timeout

    def add_item(self, item):
        self.children.append(item)


class MockButton:
    def __init__(self, label=None, style=None, custom_id=None, emoji=None, row=None, disabled=False):
        self.label = label
        self.style = style
        self.custom_id = custom_id
        self.emoji = emoji
        self.row = row
        self.callback = None
        self.disabled = disabled

    def _is_v2(self):
        return False


class TestInfirmaryUI(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        # Patch sys.modules
        self.modules_patcher = patch.dict(sys.modules)
        self.modules_patcher.start()

        # Mock Pymongo
        mock_pymongo = MagicMock()
        mock_pymongo.errors = MagicMock()
        sys.modules["pymongo"] = mock_pymongo
        sys.modules["pymongo.errors"] = mock_pymongo.errors

        # Mock Discord
        mock_discord = MagicMock()
        mock_discord.ButtonStyle.primary = "primary"
        mock_discord.ButtonStyle.secondary = "secondary"
        mock_discord.ButtonStyle.grey = "grey"
        mock_discord.Color.dark_grey.return_value = "dark_grey"
        mock_discord.Color.green.return_value = "green"
        mock_discord.Color.red.return_value = "red"

        mock_ui = MagicMock()
        mock_ui.View = MockView
        mock_ui.Button = MockButton

        sys.modules["discord"] = mock_discord
        sys.modules["discord.ui"] = mock_ui

        # Mock other dependencies
        # Ensure 'cogs' is seen as a package so importlib can reload submodule
        sys.modules["cogs"] = MagicMock()
        sys.modules["cogs.utils"] = MagicMock()
        sys.modules["cogs.utils.ui_helpers"] = MagicMock()

        # Import module under test
        import cogs.infirmary_cog
        importlib.reload(cogs.infirmary_cog)

        self.InfirmaryView = cogs.infirmary_cog.InfirmaryView
        self.DatabaseManager = cogs.infirmary_cog.DatabaseManager
        self.PlayerStats = cogs.infirmary_cog.PlayerStats

        self.mock_db = MagicMock()
        self.mock_user = MagicMock()
        self.mock_user.id = 12345

        # Setup common data
        self.stats = MagicMock()
        self.stats.max_hp = 100
        self.stats.max_mp = 50

        self.p_data = {
            "current_hp": 80,
            "current_mp": 40,
            "aurum": 500
        }

        # Calculate expected cost: (20 HP * 2) + (10 MP * 3) = 70
        # Mock the calculate_heal_cost static method on the DatabaseManager class itself
        self.DatabaseManager.calculate_heal_cost = MagicMock(return_value=70)

    def tearDown(self):
        self.modules_patcher.stop()

    def test_init_buttons(self):
        """Test buttons are initialized correctly."""
        view = self.InfirmaryView(self.mock_db, self.mock_user, self.p_data, self.stats)

        # Heal Button
        heal_btn = view.children[0]
        self.assertEqual(heal_btn.label, "Heal (70 G)")
        self.assertFalse(heal_btn.disabled)

        # Back Button
        back_btn = view.children[1]
        self.assertEqual(back_btn.label, "Return to Hall")

    def test_init_disabled_if_broke(self):
        """Test heal button disabled if insufficient funds."""
        self.p_data["aurum"] = 10  # Less than 70
        view = self.InfirmaryView(self.mock_db, self.mock_user, self.p_data, self.stats)

        heal_btn = view.children[0]
        self.assertTrue(heal_btn.disabled)
        self.assertEqual(heal_btn.label, "Insufficient Funds")

    def test_init_disabled_if_full_health(self):
        """Test heal button disabled if full health."""
        self.p_data["current_hp"] = 100
        self.p_data["current_mp"] = 50
        self.DatabaseManager.calculate_heal_cost.return_value = 0

        view = self.InfirmaryView(self.mock_db, self.mock_user, self.p_data, self.stats)

        heal_btn = view.children[0]
        self.assertTrue(heal_btn.disabled)
        self.assertEqual(heal_btn.label, "Fully Restored")

    async def test_heal_callback_success(self):
        """Test successful heal interaction."""
        view = self.InfirmaryView(self.mock_db, self.mock_user, self.p_data, self.stats)
        interaction = AsyncMock()

        # Mock execute_heal via db
        self.mock_db.execute_heal.return_value = (True, "Healed!")
        self.mock_db.get_player_stats_json.return_value = self.stats

        # Mock refresh data
        self.mock_db.get_player.return_value = self.p_data

        # We need to patch PlayerStats.from_dict to return our mock stats
        with patch.object(self.PlayerStats, 'from_dict', return_value=self.stats):
            await view.heal_callback(interaction)

        # Verify db calls
        self.mock_db.execute_heal.assert_called_with(12345, 100, 50)

        # Verify response
        interaction.edit_original_response.assert_called()
        args, kwargs = interaction.edit_original_response.call_args
        embed = kwargs['embed']
        self.assertIsNotNone(embed)

    async def test_heal_callback_failure(self):
        """Test failed heal interaction."""
        view = self.InfirmaryView(self.mock_db, self.mock_user, self.p_data, self.stats)
        interaction = AsyncMock()

        # Mock failure
        self.mock_db.get_player_stats_json.return_value = None # Cause execute_heal to fail inside _execute_heal

        await view.heal_callback(interaction)

        # Verify response
        interaction.edit_original_response.assert_called()
        args, kwargs = interaction.edit_original_response.call_args
        # Should show error state in embed
