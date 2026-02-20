import os
import sys
import unittest
from unittest.mock import MagicMock, patch
import importlib

# Add repo root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestSkillUpgradeCost(unittest.TestCase):
    def setUp(self):
        # 1. Setup Mocks
        self.mock_discord = MagicMock()

        # Capture Real Item if available
        RealItem = object
        if "discord.ui" in sys.modules:
            try:
                candidate = sys.modules["discord.ui"].Item
                if isinstance(candidate, type):
                    RealItem = candidate
            except AttributeError:
                pass

        class MockView:
            def __init__(self, timeout=180):
                pass
            def add_item(self, item):
                pass
            def clear_items(self):
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

        self.mock_discord.ui.View = MockView
        self.mock_discord.ui.Button = MockButton
        self.mock_discord.ui.Select = MockSelect

        # 2. Patch modules
        self.modules_patcher = patch.dict(sys.modules, {
            "discord": self.mock_discord,
            "discord.ui": self.mock_discord.ui,
            "discord.ext": MagicMock(),
            "discord.ext.commands": MagicMock(),
            "pymongo": MagicMock(),
        })
        self.modules_patcher.start()

        # 3. Import/Reload module
        if "cogs.skill_trainer_cog" in sys.modules:
            del sys.modules["cogs.skill_trainer_cog"]
        import cogs.skill_trainer_cog
        self.SkillTrainerView = cogs.skill_trainer_cog.SkillTrainerView
        self.get_upgrade_cost = cogs.skill_trainer_cog.get_upgrade_cost

        # Import DatabaseManager
        import database.database_manager
        self.DatabaseManager = database.database_manager.DatabaseManager

        self.mock_db = MagicMock(spec=self.DatabaseManager)
        self.user = MagicMock()
        self.user.id = 12345
        self.player_data = {"vestige_pool": 10000, "class_id": 1}

    def tearDown(self):
        self.modules_patcher.stop()

    @patch("cogs.skill_trainer_cog.SKILLS", {
        "test_skill": {
            "key_id": "test_skill",
            "name": "Test Skill",
            "upgrade_cost": 10,  # Base cost
            "class_id": 1,
            "learn_cost": 100
        }
    })
    def test_upgrade_cost_calculation(self):
        # 1. Setup: User has 'test_skill' at Level 10
        # This mocks _get_player_skills_sync used in __init__
        self.mock_db.get_all_player_skills.return_value = [
            {"skill_key": "test_skill", "skill_level": 10}
        ]

        # This mocks get_player_skill_row which SHOULD be used in _execute_upgrade (but currently isn't)
        self.mock_db.get_player_skill_row.return_value = {
            "skill_key": "test_skill", "skill_level": 10
        }

        view = self.SkillTrainerView(self.mock_db, self.user, self.player_data)

        # 2. Execute Upgrade
        # _execute_upgrade is called with the skill key
        view._execute_upgrade("test_skill")

        # 3. Assert Cost
        args, _ = self.mock_db.upgrade_skill.call_args
        # upgrade_skill(discord_id, skill_key, cost)
        called_cost = args[2]

        print(f"\n[TEST] Called Cost: {called_cost}")

        # Target: Cost should be scaled
        scaled_cost = self.get_upgrade_cost(10, 10)
        print(f"[TEST] Scaled Cost (Target): {scaled_cost}")

        self.assertEqual(called_cost, scaled_cost, f"Cost should be scaled to {scaled_cost}, got {called_cost}")

if __name__ == "__main__":
    unittest.main()
