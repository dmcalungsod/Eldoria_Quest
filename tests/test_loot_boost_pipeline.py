import sys
import unittest
from unittest.mock import MagicMock, patch

# Mock dependencies BEFORE imports
sys.modules["pymongo"] = MagicMock()
sys.modules["pymongo.errors"] = MagicMock()
sys.modules["discord"] = MagicMock()

# Import target classes (assuming correct paths)
# Note: Adjust paths if necessary based on repo structure
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game_systems.adventure.adventure_session import AdventureSession
from game_systems.adventure.adventure_rewards import AdventureRewards
from game_systems.player.player_stats import PlayerStats

class TestLootBoostPipeline(unittest.TestCase):
    def setUp(self):
        self.mock_db = MagicMock()
        self.discord_id = 123456789

    def test_adventure_session_fetches_loot_boost(self):
        """
        Regression Test: Ensure AdventureSession correctly fetches active event modifiers
        (specifically loot_boost) and includes them in the session context.
        """
        # 1. Setup Mock DB Bundle
        # We need a valid bundle structure for _fetch_session_context
        bundle = {
            "stats": {"STR": {"base": 10}, "HP": {"base": 100}, "MP": {"base": 50}},
            "buffs": [],
            "player": {"current_hp": 100, "current_mp": 50, "level": 1},
            "skills": [],
        }
        self.mock_db.get_combat_context_bundle.return_value = bundle

        # Mock active global boosts (empty for now)
        self.mock_db.get_active_boosts.return_value = []

        # 2. Mock WorldEventSystem via db.get_active_world_event (or patch the class)
        # AdventureSession uses: event_system = WorldEventSystem(self.db); event = event_system.get_current_event()
        # WorldEventSystem calls self.db.get_active_world_event()

        # We need to patch WorldEventSystem to control get_current_event directly,
        # or mock db.get_active_world_event if WorldEventSystem relies on it.
        # Let's check how WorldEventSystem is implemented. It uses db.get_active_world_event.

        active_event = {
            "type": "treasure_hunt",
            "active": 1,
            "modifiers": {"loot_boost": 1.5}
        }

        # We need to patch where WorldEventSystem is imported in AdventureSession
        # or rely on mocking the DB call inside WorldEventSystem.
        # Since we pass mock_db to AdventureSession, and it passes it to WorldEventSystem,
        # mocking db.get_active_world_event is the cleanest way if WorldEventSystem uses it.
        # Based on previous read, WorldEventSystem(db) calls db.get_active_world_event().

        # However, AdventureSession instantiates WorldEventSystem internally.
        # Let's patch WorldEventSystem in game_systems.adventure.adventure_session

        with patch("game_systems.adventure.adventure_session.WorldEventSystem") as MockWES:
            mock_wes_instance = MockWES.return_value
            mock_wes_instance.get_current_event.return_value = active_event

            # 3. Instantiate Session
            session = AdventureSession(self.mock_db, MagicMock(), MagicMock(), self.discord_id)

            # 4. Execute
            context = session._fetch_session_context(bundle)

            # 5. Assert
            self.assertIsNotNone(context, "Context should not be None")
            self.assertIn("active_boosts", context)
            self.assertEqual(context["active_boosts"].get("loot_boost"), 1.5,
                             "Loot boost from event modifier should be present in context")

    def test_adventure_rewards_uses_loot_boost(self):
        """
        Regression Test: Ensure AdventureRewards extracts loot_boost from combat_result
        and passes it to LootCalculator.
        """
        # 1. Setup AdventureRewards
        rewards = AdventureRewards(self.mock_db, self.discord_id)

        # Mock PlayerStats
        self.mock_db.get_player_stats_json.return_value = {"STR": {"base": 10}, "LCK": {"base": 50}}

        # 2. Prepare Inputs
        combat_result = {
            "exp": 100,
            "active_boosts": {"loot_boost": 2.5},
            "drops": [("material_a", 0.5)],
            "monster_data": {"name": "Test Monster", "tier": "Normal"}
        }

        # 3. Patch LootCalculator
        with patch("game_systems.adventure.adventure_rewards.LootCalculator") as MockLC:
            MockLC.roll_drops.return_value = ["material_a"]

            # 4. Execute
            # We call _process_loot_and_quests directly for focused testing
            # or process_victory if we want integration. _process_loot_and_quests is simpler for unit test.
            # But process_victory is public. Let's use _process_loot_and_quests as it returns drops.

            quest_system = MagicMock()
            inventory_manager = MagicMock()
            session_loot = {}
            logs = []

            rewards._process_loot_and_quests(combat_result, quest_system, inventory_manager, session_loot, logs)

            # 5. Assert
            # Verify roll_drops was called with correct boost
            # Signature: roll_drops(drops_list, luck, loot_boost)
            args, _ = MockLC.roll_drops.call_args

            # drops_list is args[0]
            # luck is args[1]
            # loot_boost is args[2]

            self.assertEqual(args[2], 2.5, f"Expected loot_boost=2.5, got {args[2]}")

            # Verify luck is passed correctly (50 from mocked stats)
            # Note: PlayerStats.from_dict might adjust values.
            # Base 50 LCK -> 50 Luck if no other modifiers.
            # Let's verify it's close to 50.
            self.assertEqual(args[1], 50, f"Expected luck=50, got {args[1]}")

if __name__ == "__main__":
    unittest.main()
