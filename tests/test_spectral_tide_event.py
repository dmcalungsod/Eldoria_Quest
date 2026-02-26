import datetime
import sys
import unittest
from unittest.mock import MagicMock, patch

# Mock modules before importing
sys.modules["pymongo"] = MagicMock()
sys.modules["pymongo.errors"] = MagicMock()
sys.modules["discord"] = MagicMock()

from game_systems.adventure.adventure_rewards import AdventureRewards  # noqa: E402
from game_systems.adventure.adventure_session import AdventureSession  # noqa: E402
from game_systems.core.world_time import TimePhase  # noqa: E402
from game_systems.events.world_event_system import WorldEventSystem  # noqa: E402


class TestSpectralTideEvent(unittest.TestCase):
    def setUp(self):
        self.mock_db = MagicMock()
        self.system = WorldEventSystem(self.mock_db)

        # Patch WorldTime
        self.patcher = patch("game_systems.events.world_event_system.WorldTime")
        self.mock_world_time = self.patcher.start()
        self.mock_world_time.now.side_effect = datetime.datetime.now

        # Patch AdventureSession dependencies
        self.mock_quest = MagicMock()
        self.mock_inv = MagicMock()

    def tearDown(self):
        self.patcher.stop()

    def test_start_spectral_tide_event(self):
        """Verify we can start the event and it has correct modifiers."""
        success = self.system.start_event(WorldEventSystem.SPECTRAL_TIDE, 24)
        self.assertTrue(success)
        self.mock_db.set_active_world_event.assert_called_with(
            WorldEventSystem.SPECTRAL_TIDE, unittest.mock.ANY, unittest.mock.ANY
        )

        # Mock DB returning the event
        self.mock_db.get_active_world_event.return_value = {
            "type": WorldEventSystem.SPECTRAL_TIDE,
            "end_time": "2099-01-01T00:00:00",
            "active": 1,
        }

        event = self.system.get_current_event()
        self.assertEqual(event["name"], "The Spectral Tide")
        self.assertEqual(event["modifiers"]["spectral_ambush_chance"], 0.15)
        self.assertEqual(event["modifiers"]["night_danger_mod"], 0.10)

    @patch("game_systems.adventure.adventure_session.AdventureRewards")
    @patch("game_systems.adventure.adventure_session.CombatHandler")
    @patch("game_systems.adventure.adventure_session.EventHandler")
    @patch("game_systems.adventure.adventure_session.WorldTime")
    @patch("random.randint")
    def test_adventure_session_night_danger(self, mock_randint, mock_time, mock_event, mock_combat, mock_rewards):
        """Verify AdventureSession triggers combat more often at night during Spectral Tide."""
        discord_id = 123
        session = AdventureSession(self.mock_db, self.mock_quest, self.mock_inv, discord_id)
        session.location_id = "forest_outskirts"
        session.active_monster = None

        # Setup Context
        bundle = {
            "stats": {"HP": 100, "MP": 100},
            "buffs": [],
            "player": {"current_hp": 100, "current_mp": 100},
            "skills": [],
        }
        self.mock_db.get_combat_context_bundle.return_value = bundle

        # Mock Event Active with modifiers
        # Note: _fetch_session_context calls self.db.get_active_world_event
        self.mock_db.get_active_world_event.return_value = {
            "type": WorldEventSystem.SPECTRAL_TIDE,
            "end_time": "2099-01-01T00:00:00",
            "active": 1,
        }
        self.mock_db.get_active_boosts.return_value = []  # Standard boosts empty

        # Mock Time to NIGHT
        mock_time.get_current_phase.return_value = TimePhase.NIGHT
        mock_time.get_current_weather.return_value = "Clear"

        # Base REGEN_CHANCE = 40
        # Night (-10) = 30
        # Event Mod (+10% danger = -10 regen) = 20
        # So threshold is 20.
        # If random.randint(1, 100) returns 25:
        # 25 > 20 -> True (Combat)
        # Without event (Threshold 30): 25 > 30 -> False (No Combat)

        mock_randint.return_value = 25  # Should trigger combat with event

        # Mock Combat Init to return something
        mock_combat_instance = mock_combat.return_value
        mock_combat_instance.initiate_combat.return_value = ({"name": "Ghost"}, "A ghost appears!")

        # Execute
        result = session.simulate_step(action=None)

        # Verify Combat Initiated
        self.assertEqual(session.active_monster["name"], "Ghost")
        mock_combat_instance.initiate_combat.assert_called()

    @patch("game_systems.adventure.adventure_rewards.LootCalculator")
    @patch("random.random")
    @patch("random.randint")
    def test_adventure_rewards_drops_ectoplasm(self, mock_randint, mock_random, mock_loot_calc):
        """Verify AdventureRewards drops ectoplasm during Spectral Tide."""
        rewards = AdventureRewards(self.mock_db, 123)

        # Mock Event Active
        self.mock_db.get_active_world_event.return_value = {
            "type": WorldEventSystem.SPECTRAL_TIDE,
            "end_time": "2099-01-01T00:00:00",
            "active": 1,
        }
        # Mock Stat XP json load
        self.mock_db.get_stat_exp_row.return_value = None  # Skip stat xp
        # Mock Achievement Check
        rewards.achievement_system = MagicMock()
        rewards.achievement_system.check_kill_achievements.return_value = None
        rewards.achievement_system.check_group_achievements.return_value = None
        # Mock Faction
        rewards.faction_system = MagicMock()
        rewards.faction_system.grant_reputation_for_kill.return_value = []

        # Mock Random for drops
        # First call is checked against 0.3
        mock_random.return_value = 0.1

        # ecto_count = random.randint(1, 2)
        mock_randint.return_value = 2

        # Setup Inputs
        combat_result = {
            "exp": 100,
            "drops": [],
            "monster_data": {"name": "Test", "tier": "Normal"},
            "active_boosts": {},
        }
        self.mock_db.get_player_stats_json.return_value = {"luck": 10}
        self.mock_db.get_player_quests.return_value = []
        mock_loot_calc.roll_drops.return_value = []
        session_loot = {}

        # Execute
        logs = rewards.process_victory(
            battle_report={},
            report_list=[],
            combat_result=combat_result,
            quest_system=self.mock_quest,
            inventory_manager=self.mock_inv,
            session_loot=session_loot,
            location_id="forest_outskirts",
        )

        # Verify Ectoplasm dropped in SESSION LOOT
        self.assertIn("ectoplasm", session_loot)
        self.assertEqual(session_loot["ectoplasm"], 2)

        # Verify Logs contain Ectoplasm
        log_str = "\n".join(logs)
        self.assertIn("Ectoplasm", log_str)
