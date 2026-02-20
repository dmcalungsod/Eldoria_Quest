import sys
import unittest
import importlib
from unittest.mock import MagicMock

# 1. Create fresh mocks
mock_discord = MagicMock()

class MockButtonStyle:
    danger = "danger"
    success = "success"
    secondary = "secondary"
    primary = "primary"

mock_discord.ButtonStyle = MockButtonStyle
mock_discord.Color.dark_red.return_value = "dark_red"
mock_discord.Color.dark_green.return_value = "dark_green"
mock_discord.Color.dark_grey.return_value = "dark_grey"

# Define mock classes explicitly
class MockView:
    def __init__(self, timeout=None):
        self.children = []
        self.timeout = timeout
    def add_item(self, item):
        self.children.append(item)

class MockButton:
    def __init__(self, label=None, style=None, custom_id=None, emoji=None, row=None):
        self.label = label
        self.style = style
        self.custom_id = custom_id
        self.emoji = emoji
        self.row = row
        self.callback = None
        self.disabled = False

    def _is_v2(self):
        return False

mock_discord.ui = MagicMock()
mock_discord.ui.View = MockView
mock_discord.ui.Button = MockButton

# 2. Mock Dependencies in sys.modules
sys.modules["discord"] = mock_discord
sys.modules["discord.ui"] = mock_discord.ui
sys.modules["pymongo"] = MagicMock()
sys.modules["cogs"] = MagicMock()
sys.modules["cogs.ui_helpers"] = MagicMock()
sys.modules["game_systems.adventure.ui.adventure_embeds"] = MagicMock()

# 3. Import and Patch
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import module
import game_systems.adventure.ui.exploration_view as ev_module
# Reload to ensure fresh start
importlib.reload(ev_module)

# PATCH DIRECTLY ON THE IMPORTED MODULE
ev_module.discord = mock_discord
# Also patch Button/View if they were imported via 'from ... import'
ev_module.Button = MockButton
ev_module.View = MockView

from game_systems.adventure.ui.exploration_view import ExplorationView


class TestExplorationViewUX(unittest.TestCase):
    def setUp(self):
        self.mock_db = MagicMock()
        self.mock_manager = MagicMock()
        self.mock_user = MagicMock()
        self.mock_user.id = 12345

        # Mock PlayerStats
        self.stats = MagicMock()
        self.stats.max_hp = 100

    def test_forward_button_safe(self):
        """Standard safe state: No monster, high HP."""
        vitals = {"current_hp": 100, "current_mp": 50}

        view = ExplorationView(
            self.mock_db,
            self.mock_manager,
            "loc_1",
            [],
            self.mock_user,
            self.stats,
            vitals=vitals,
            active_monster=None
        )

        # Check Forward Button (index 0)
        btn = view.children[0]
        self.assertEqual(btn.label, "Forward")
        self.assertEqual(btn.style, "success")

    def test_forward_button_danger(self):
        """Danger state: No monster, LOW HP (<30%)."""
        vitals = {"current_hp": 20, "current_mp": 50} # 20/100 = 20%

        view = ExplorationView(
            self.mock_db,
            self.mock_manager,
            "loc_1",
            [],
            self.mock_user,
            self.stats,
            vitals=vitals,
            active_monster=None
        )

        btn = view.children[0]
        self.assertEqual(btn.label, "Forward")
        self.assertEqual(btn.style, "danger", "Button should be red (danger) when HP is low")

    def test_battle_state(self):
        """Battle state: Active monster overrides HP danger."""
        vitals = {"current_hp": 10, "current_mp": 50} # 10% HP (Critical)
        monster = {"name": "Goblin", "hp": 50}

        view = ExplorationView(
            self.mock_db,
            self.mock_manager,
            "loc_1",
            [],
            self.mock_user,
            self.stats,
            vitals=vitals,
            active_monster=monster
        )

        btn = view.children[0]
        self.assertEqual(btn.label, "Battle")
        self.assertEqual(btn.style, "danger")

if __name__ == "__main__":
    unittest.main()
