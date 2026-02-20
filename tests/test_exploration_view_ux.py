import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add repo root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestExplorationViewUX(unittest.TestCase):
    def setUp(self):
        # 1. Mock dependencies
        self.mock_discord = MagicMock()
        self.mock_discord.ButtonStyle.success = "success"
        self.mock_discord.ButtonStyle.danger = "danger"
        self.mock_discord.ButtonStyle.secondary = "secondary"
        self.mock_discord.ButtonStyle.primary = "primary"
        self.mock_discord.Color.dark_red.return_value = "dark_red"
        self.mock_discord.Color.dark_green.return_value = "dark_green"
        self.mock_discord.Color.dark_grey.return_value = "dark_grey"

        # Mock View/Button logic
        class MockView:
            def __init__(self, timeout=None):
                self.children = []
                self.timeout = timeout
            def add_item(self, item):
                self.children.append(item)
            def clear_items(self):
                self.children.clear()

        class MockButton:
            def __init__(self, label=None, style=None, custom_id=None, emoji=None, row=None):
                self.label = label
                self.style = style
                self.custom_id = custom_id
                self.emoji = emoji
                self.row = row
                self.callback = None
                self.disabled = False

        class MockSelect:
            def __init__(self, placeholder=None, min_values=1, max_values=1, options=None, row=None, custom_id=None):
                self.placeholder = placeholder
                self.min_values = min_values
                self.max_values = max_values
                self.options = options
                self.row = row
                self.custom_id = custom_id
                self.callback = None
                self.disabled = False
                self.values = []

        class MockSelectOption:
            def __init__(self, label=None, value=None, description=None, emoji=None, default=False):
                self.label = label
                self.value = value
                self.description = description
                self.emoji = emoji
                self.default = default

        self.mock_discord.SelectOption = MockSelectOption
        self.mock_discord.ui.View = MockView
        self.mock_discord.ui.Button = MockButton
        self.mock_discord.ui.Select = MockSelect

        # Patch sys.modules
        self.modules_patcher = patch.dict(sys.modules, {
            "discord": self.mock_discord,
            "discord.ui": self.mock_discord.ui,
            "pymongo": MagicMock(),
            "cogs.ui_helpers": MagicMock(),
            "game_systems.adventure.ui.adventure_embeds": MagicMock(),
        })
        self.modules_patcher.start()

        # Import module under test
        if "game_systems.adventure.ui.exploration_view" in sys.modules:
            del sys.modules["game_systems.adventure.ui.exploration_view"]

        import game_systems.adventure.ui.exploration_view
        self.ExplorationView = game_systems.adventure.ui.exploration_view.ExplorationView

        self.mock_db = MagicMock()
        self.mock_manager = MagicMock()
        self.mock_user = MagicMock()
        self.mock_user.id = 12345

        # Mock PlayerStats
        self.stats = MagicMock()
        self.stats.max_hp = 100

    def tearDown(self):
        self.modules_patcher.stop()

    def test_forward_button_safe(self):
        """Standard safe state: No monster, high HP."""
        vitals = {"current_hp": 100, "current_mp": 50}

        view = self.ExplorationView(
            self.mock_db,
            self.mock_manager,
            "loc_1",
            [],
            self.mock_user,
            self.stats,
            vitals=vitals,
            active_monster=None,
            class_id=1,
        )

        # Check Forward Button (index 0)
        btn = view.children[0]
        self.assertEqual(btn.label, "Forward")
        self.assertEqual(btn.style, "success")

    def test_forward_button_danger(self):
        """Danger state: No monster, LOW HP (<30%)."""
        vitals = {"current_hp": 20, "current_mp": 50}  # 20/100 = 20%

        view = self.ExplorationView(
            self.mock_db,
            self.mock_manager,
            "loc_1",
            [],
            self.mock_user,
            self.stats,
            vitals=vitals,
            active_monster=None,
            class_id=1,
        )

        btn = view.children[0]
        self.assertEqual(btn.label, "Forward")
        self.assertEqual(btn.style, "danger", "Button should be red (danger) when HP is low")

    def test_battle_state(self):
        """Battle state: Active monster overrides HP danger."""
        vitals = {"current_hp": 10, "current_mp": 50}  # 10% HP (Critical)
        monster = {"name": "Goblin", "hp": 50}

        view = self.ExplorationView(
            self.mock_db,
            self.mock_manager,
            "loc_1",
            [],
            self.mock_user,
            self.stats,
            vitals=vitals,
            active_monster=monster,
            class_id=1,
        )

        # Updated: Now expects "Attack" button
        btn = view.children[0]
        self.assertEqual(btn.label, "Attack")
        self.assertEqual(btn.style, "danger")

        # Check for Special Ability Button
        # Items: Attack, Defend, Flee, Pack, Special, Stance Select
        special_btn = view.children[4]
        self.assertEqual(special_btn.style, "primary")
        self.assertTrue(hasattr(special_btn, "callback"))

        # Check for Stance Select (should be last now)
        stance_select = view.children[-1]
        self.assertEqual(stance_select.custom_id, "stance_select")

    def test_battle_state_with_skills(self):
        """Battle state: Active monster + Skills = Select Menu."""
        vitals = {"current_hp": 100, "current_mp": 50}
        monster = {"name": "Goblin", "hp": 50}
        skills = [
            {"name": "Fireball", "key_id": "fireball", "type": "Active", "mp_cost": 10},
            {"name": "Heal", "key_id": "heal", "type": "Active", "mp_cost": 5},
        ]

        view = self.ExplorationView(
            self.mock_db,
            self.mock_manager,
            "loc_1",
            [],
            self.mock_user,
            self.stats,
            vitals=vitals,
            active_monster=monster,
            class_id=1,
            skills=skills,
        )

        # Check for Skill Select Menu (should be last)
        # Items: Attack, Defend, Flee, Pack, Special, Stance Select, Skill Select
        select_menu = view.children[-1]
        self.assertEqual(select_menu.custom_id, "skill_select")
        self.assertEqual(len(select_menu.options), 2)
        self.assertEqual(select_menu.options[0].label, "Fireball")
        self.assertEqual(select_menu.options[0].emoji, "✨")
        self.assertEqual(select_menu.options[1].label, "Heal")
        self.assertEqual(select_menu.options[1].emoji, "💚")

        # Check for Stance Select (should be second to last)
        stance_select = view.children[-2]
        self.assertEqual(stance_select.custom_id, "stance_select")


if __name__ == "__main__":
    unittest.main()
