import os
import sys
import unittest
from unittest.mock import MagicMock

# Add repo root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock external dependencies
pymongo_mock = MagicMock()
pymongo_errors_mock = MagicMock()
pymongo_mock.errors = pymongo_errors_mock
sys.modules["pymongo"] = pymongo_mock
sys.modules["pymongo.errors"] = pymongo_errors_mock
sys.modules["discord"] = MagicMock()

# Now import the modules
from game_systems.adventure.combat_handler import CombatHandler  # noqa: E402
from database.database_manager import DatabaseManager  # noqa: E402


class TestCombatCrash(unittest.TestCase):
    def test_resolve_turn_db_failure(self):
        """Test that resolve_turn handles database failures without crashing due to UnboundLocalError."""

        # Instantiate handler with a mocked DB
        db_mock = MagicMock(spec=DatabaseManager)

        # Simulate DB failure early in the process
        db_mock.get_player_stats_json.side_effect = Exception(
            "Database Connection Failed"
        )

        handler = CombatHandler(db_mock, 12345)

        active_monster = {"HP": 100, "max_hp": 100}
        battle_report = CombatHandler.create_empty_battle_report()

        try:
            result = handler.resolve_turn(
                active_monster=active_monster,
                battle_report=battle_report,
                accumulated_exp=0,
            )

            # If we reach here, we check if the result is valid
            print(f"Result: {result}")
            self.assertIsNone(result["winner"])
            self.assertEqual(
                result["phrases"][0], "*Something disrupts the flow of battle...*"
            )

        except UnboundLocalError as e:
            # THIS IS EXPECTED TO FAIL currently
            print(f"Caught expected UnboundLocalError: {e}")
            raise  # Re-raise to fail the test and confirm the bug
        except Exception as e:
            self.fail(f"CombatHandler crashed with unexpected exception: {e}")


if __name__ == "__main__":
    unittest.main()
