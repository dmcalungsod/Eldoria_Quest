import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add repo root to path
sys.path.append(os.getcwd())


# --- MOCK DISCORD ---
class MockView:
    def __init__(self, timeout=180):
        pass

    def add_item(self, item):
        pass

    def clear_items(self):
        pass


# Capture Real Item if available
RealItem = object
if "discord.ui" in sys.modules:
    try:
        RealItem = sys.modules["discord.ui"].Item
    except AttributeError:
        pass


class MockButton(RealItem):
    def __init__(self, label=None, style=None, custom_id=None, emoji=None, row=None, disabled=False):
        self.callback = None
        self.label = label

    def _is_v2(self):
        return False


class MockSelect(RealItem):
    def __init__(self, placeholder=None, min_values=1, max_values=1, row=None, disabled=False):
        self.callback = None
        self.options = []
        self.disabled = disabled

    def add_option(self, label, value, description=None, emoji=None):
        self.options.append((label, value))


discord = MagicMock()
discord.ui.View = MockView
discord.ui.Button = MockButton
discord.ui.Select = MagicMock(side_effect=lambda *args, **kwargs: MockSelect(*args, **kwargs))
discord.ButtonStyle = MagicMock()
discord.User = MagicMock()
discord.Embed = MagicMock()
discord.Color = MagicMock()

sys.modules["discord"] = discord
sys.modules["discord.ui"] = discord.ui
sys.modules["discord.ext"] = MagicMock()
sys.modules["discord.ext.commands"] = MagicMock()

# --- IMPORT MODULE UNDER TEST (force reload to pick up our mocks) ---
import importlib
import cogs.skill_trainer_cog as _stc_mod

importlib.reload(_stc_mod)

from cogs.skill_trainer_cog import SkillTrainerView, get_upgrade_cost  # noqa: E402
from database.database_manager import DatabaseManager  # noqa: E402


class TestSkillUpgradeCost(unittest.TestCase):
    def setUp(self):
        self.mock_db = MagicMock(spec=DatabaseManager)
        self.user = MagicMock()
        self.user.id = 12345
        self.player_data = {"vestige_pool": 10000, "class_id": 1}

    @patch(
        "cogs.skill_trainer_cog.SKILLS",
        {
            "test_skill": {
                "key_id": "test_skill",
                "name": "Test Skill",
                "upgrade_cost": 10,  # Base cost
                "class_id": 1,
                "learn_cost": 100,
            }
        },
    )
    def test_upgrade_cost_calculation(self):
        # 1. Setup: User has 'test_skill' at Level 10
        # This mocks _get_player_skills_sync used in __init__
        self.mock_db.get_all_player_skills.return_value = [{"skill_key": "test_skill", "skill_level": 10}]

        # This mocks get_player_skill_row which SHOULD be used in _execute_upgrade (but currently isn't)
        self.mock_db.get_player_skill_row.return_value = {"skill_key": "test_skill", "skill_level": 10}

        view = SkillTrainerView(self.mock_db, self.user, self.player_data)

        # Mock upgrade_skill to return a proper tuple
        self.mock_db.upgrade_skill.return_value = (True, "Upgraded!", 11)

        # 2. Execute Upgrade
        # _execute_upgrade is called with the skill key
        view._execute_upgrade("test_skill")

        # 3. Assert Cost
        # Expected incorrect behavior: Cost is base_cost (10)
        # Correct behavior would be: 10 * 10^1.8 approx 631

        args, _ = self.mock_db.upgrade_skill.call_args
        # upgrade_skill(discord_id, skill_key, cost)
        called_cost = args[2]

        print(f"\n[TEST] Called Cost: {called_cost}")

        # Target: Cost should be scaled
        scaled_cost = get_upgrade_cost(10, 10)
        print(f"[TEST] Scaled Cost (Target): {scaled_cost}")

        self.assertEqual(called_cost, scaled_cost, f"Cost should be scaled to {scaled_cost}, got {called_cost}")


if __name__ == "__main__":
    unittest.main()
