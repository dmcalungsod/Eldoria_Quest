import os
import sys
import unittest
from unittest.mock import MagicMock

# Add root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock Discord Modules
discord_mock = MagicMock()
sys.modules['discord'] = discord_mock
sys.modules['discord.ext'] = MagicMock()
sys.modules['discord.ext.commands'] = MagicMock()

# create a dummy View class so inheritance works properly
class MockView:
    def __init__(self, timeout=None):
        self.children = []
    def add_item(self, item):
        self.children.append(item)
    def stop(self):
        pass

discord_ui = MagicMock()
discord_ui.View = MockView
# Also need Button and Select to be importable
discord_ui.Button = MagicMock
discord_ui.Select = MagicMock
sys.modules['discord.ui'] = discord_ui

# Mock DatabaseManager
sys.modules['database.database_manager'] = MagicMock()

# Now import the module under test
# We need to ensure SKILLS is importable
try:
    from game_systems.data.skills_data import SKILLS
except ImportError:
    # If not running from root, adjust path (but we assume running from root)
    pass

from cogs.skill_trainer_cog import SkillTrainerView, get_upgrade_cost  # noqa: E402


class TestSkillTrainerSecurity(unittest.TestCase):
    def setUp(self):
        self.mock_db = MagicMock()
        self.mock_user = MagicMock()
        self.mock_user.id = 12345
        self.mock_player_data = {"vestige_pool": 10000, "class_id": 1}

        # Mock connection and cursor
        self.mock_conn = MagicMock()
        self.mock_db.get_connection.return_value.__enter__.return_value = self.mock_conn

        # Ensure _get_player_skills_sync returns empty dict effectively
        # It calls conn.execute(...).fetchall()
        # We make sure fetchall returns empty list initially
        self.mock_conn.execute.return_value.fetchall.return_value = []

        # Instantiate View
        self.view = SkillTrainerView(self.mock_db, self.mock_user, self.mock_player_data)

    def test_execute_learn_security(self):
        # Let's pick a skill with a cost > 0 for better test
        skill_key = "cleave"
        real_cost = SKILLS[skill_key]["learn_cost"] # 2000

        # Mock DB
        def side_effect(sql, params=None):
            if "SELECT vestige_pool" in sql:
                return MagicMock(fetchone=lambda: {"vestige_pool": 10000})
            return MagicMock()
        self.mock_conn.execute.side_effect = side_effect

        # Call the method
        import inspect
        sig = inspect.signature(self.view._execute_learn)
        print(f"DEBUG: Sig parameters: {list(sig.parameters.keys())}")

        if 'cost' in sig.parameters:
            print("VULNERABLE: _execute_learn accepts 'cost'")
            # Pass 0 as cost to simulate attack
            success, msg = self.view._execute_learn(skill_key, 0)
        else:
            print("SECURE: _execute_learn ignores 'cost'")
            success, msg = self.view._execute_learn(skill_key)

        # Verify DB interactions
        calls = self.mock_conn.execute.call_args_list
        found_deduction = False
        deducted_amount = -1

        for call in calls:
            sql = call[0][0]
            params = call[0][1]
            if "UPDATE players SET vestige_pool" in sql:
                deducted_amount = params[0]
                found_deduction = True

        if found_deduction:
            print(f"Deducted Amount: {deducted_amount}")
            if deducted_amount == real_cost:
                print("PASS: Correct cost deducted.")
            else:
                print(f"FAIL: Deducted {deducted_amount}, expected {real_cost}")
        else:
            print("FAIL: No deduction found.")

    def test_execute_upgrade_security(self):
        skill_key = "power_strike"
        base_upgrade_cost = SKILLS[skill_key]["upgrade_cost"] # 200
        current_level = 1
        expected_cost = get_upgrade_cost(base_upgrade_cost, current_level)

        # Mock DB
        def side_effect(sql, params=None):
            if "SELECT vestige_pool" in sql:
                return MagicMock(fetchone=lambda: {"vestige_pool": 10000})
            if "SELECT skill_level" in sql:
                # Used in secure version
                return MagicMock(fetchone=lambda: {"skill_level": current_level})
            return MagicMock()

        self.mock_conn.execute.side_effect = side_effect

        # Call the method
        import inspect
        sig = inspect.signature(self.view._execute_upgrade)

        if 'cost' in sig.parameters:
            print("VULNERABLE: _execute_upgrade accepts 'cost'")
            # Pass fake cost (0) and fake new level (99)
            success, msg = self.view._execute_upgrade(skill_key, 0, 99)
        else:
            print("SECURE: _execute_upgrade ignores 'cost'")
            success, msg = self.view._execute_upgrade(skill_key)

        # Verify DB interactions
        calls = self.mock_conn.execute.call_args_list
        found_deduction = False
        deducted_amount = -1
        found_upgrade = False
        new_level_set = -1

        for call in calls:
            sql = call[0][0]
            params = call[0][1]
            if "UPDATE players SET vestige_pool" in sql:
                deducted_amount = params[0]
                found_deduction = True
            if "UPDATE player_skills SET skill_level" in sql:
                new_level_set = params[0]
                found_upgrade = True

        if found_deduction:
            print(f"Upgrade Deducted Amount: {deducted_amount}")
            if deducted_amount == expected_cost:
                print("PASS: Correct upgrade cost deducted.")
            else:
                print(f"FAIL: Deducted {deducted_amount}, expected {expected_cost}")

        if found_upgrade:
            print(f"New Level Set: {new_level_set}")
            if new_level_set == current_level + 1:
                print("PASS: Correct new level set.")
            else:
                print(f"FAIL: Set level {new_level_set}, expected {current_level + 1}")

if __name__ == '__main__':
    unittest.main()
