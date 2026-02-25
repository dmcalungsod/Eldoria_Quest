import sys
import unittest
from unittest.mock import MagicMock, patch

# Mock modules
sys.modules["discord"] = MagicMock()
sys.modules["pymongo"] = MagicMock()
sys.modules["pymongo.errors"] = MagicMock()

from game_systems.adventure.adventure_session import AdventureSession
from game_systems.adventure.combat_handler import CombatHandler

class TestMissingBuffs(unittest.TestCase):
    def test_buffs_missing_in_auto_combat(self):
        # Setup
        mock_db = MagicMock()
        mock_discord_id = 12345

        # Mock Session Context
        context = {
            "player_stats": MagicMock(),
            "stats_dict": {"HP": 100, "MP": 100, "STR": 10},
            "vitals": {"current_hp": 100, "current_mp": 100},
            "player_row": {"level": 1, "experience": 0, "exp_to_next": 100, "class_id": 1},
            "skills": [{"name": "Rage", "key": "rage"}],
            "active_boosts": {},
            "buffs": [], # Initially empty
            "base_stats_dict": {"HP": 100, "MP": 100, "STR": 10}
        }

        mock_db.get_player_stats_json.return_value = {"HP": 100, "MP": 100, "STR": 10}
        mock_db.get_player_vitals.return_value = {"current_hp": 100, "current_mp": 100}

        # Create Session and Handler
        session = AdventureSession(mock_db, MagicMock(), MagicMock(), mock_discord_id)
        # Mock active monster to force combat
        session.active_monster = {"name": "Goblin", "hp": 50, "max_hp": 50, "atk": 5}

        # Patch CombatEngine
        with patch("game_systems.adventure.combat_handler.CombatEngine") as MockEngineCls:
            mock_engine_instance = MockEngineCls.return_value

            # Scenario:
            # Turn 1: Player uses Rage -> gets buff.
            # Turn 2: Player attacks -> should have buff.

            # Turn 1 Result
            result_turn_1 = {
                "winner": None,
                "phrases": ["Used Rage!"],
                "hp_current": 100,
                "mp_current": 90,
                "monster_hp": 50,
                "turn_report": {},
                "new_buffs": [{"name": "Rage", "stat": "STR", "amount": 10, "duration": 3}],
                "new_titles": []
            }

            # Turn 2 Result
            result_turn_2 = {
                "winner": None,
                "phrases": ["Attacked!"],
                "hp_current": 100,
                "mp_current": 90,
                "monster_hp": 40,
                "turn_report": {},
                "new_buffs": [],
                "new_titles": []
            }

            mock_engine_instance.run_combat_turn.side_effect = [result_turn_1, result_turn_2, result_turn_2]

            # Run Auto Combat
            session._resolve_auto_combat(context=context)

            # Verification
            # Check call args for CombatEngine.__init__
            # Call 1: Should have empty active_buffs (from context)
            # Call 2: Should have Rage buff?

            calls = MockEngineCls.call_args_list
            self.assertGreaterEqual(len(calls), 2, "CombatEngine should be called at least twice")

            # Inspect Turn 2 Init (index 1)
            args, kwargs = calls[1]
            active_buffs_turn_2 = kwargs.get("active_buffs", [])

            print(f"Turn 2 Active Buffs: {active_buffs_turn_2}")

            # We expect the Rage buff to be present
            has_rage = any(b["name"] == "Rage" for b in active_buffs_turn_2)
            self.assertTrue(has_rage, "Rage buff from Turn 1 should be active in Turn 2")

if __name__ == "__main__":
    unittest.main()
