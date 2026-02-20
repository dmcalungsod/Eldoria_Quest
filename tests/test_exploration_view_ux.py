import sys
import unittest
import importlib
from unittest.mock import MagicMock

# 1. Mock Discord
# We need to aggressively patch discord BEFORE importing anything that uses it
mock_discord = MagicMock()
mock_discord.ButtonStyle.success = "success"
mock_discord.ButtonStyle.danger = "danger"
mock_discord.ButtonStyle.secondary = "secondary"
mock_discord.ButtonStyle.primary = "primary"
mock_discord.Color.dark_red.return_value = "dark_red"
mock_discord.Color.dark_green.return_value = "dark_green"
mock_discord.Color.dark_grey.return_value = "dark_grey"

# Capture Real Item if available (for inheritance compatibility)
RealItem = object
if "discord.ui" in sys.modules:
    try:
        RealItem = sys.modules["discord.ui"].Item
    except AttributeError:
        pass

# Forcefully remove discord if it's already loaded to ensure mocks take precedence
if "discord" in sys.modules:
    del sys.modules["discord"]
if "discord.ui" in sys.modules:
    del sys.modules["discord.ui"]

sys.modules["discord"] = mock_discord
sys.modules["discord.ui"] = MagicMock()

# Mock View and Button
class MockView:
    def __init__(self, timeout=None):
        self.children = []
        self.timeout = timeout
    def add_item(self, item):
        self.children.append(item)

class MockButton(RealItem):
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

sys.modules["discord.ui"].View = MockView
sys.modules["discord.ui"].Button = MockButton

# 2. Mock Dependencies
sys.modules["pymongo"] = MagicMock()
sys.modules["cogs"] = MagicMock()
sys.modules["cogs.ui_helpers"] = MagicMock()
# We don't want to mock ExplorationView, but we do want to mock AdventureEmbeds
sys.modules["game_systems.adventure.ui.adventure_embeds"] = MagicMock()

# 3. Add path and Import
import os  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import game_systems.adventure.ui.exploration_view  # noqa: E402
# Force reload to ensure it picks up the mocked discord module
importlib.reload(game_systems.adventure.ui.exploration_view)
from game_systems.adventure.ui.exploration_view import ExplorationView  # noqa: E402


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

        # Instantiate with vitals as positional (assuming signature change) or kwarg
        # Currently, if we pass vitals as positional, it will crash if __init__ isn't updated.
        # So this test expects the FUTURE state of the code.

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
