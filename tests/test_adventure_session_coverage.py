import unittest
from unittest.mock import MagicMock, patch

from game_systems.adventure.adventure_session import AdventureSession
from game_systems.core.world_time import Weather


class TestAdventureSessionCoverage(unittest.TestCase):
    def setUp(self):
        self.mock_db = MagicMock()
        self.mock_qs = MagicMock()
        self.mock_im = MagicMock()
        self.discord_id = 12345

        # Default mocked row data
        self.row_data = {
            "location_id": "forest",
            "active": 1,
            "version": 1,
            "steps_completed": 5,
            "logs": "[]",
            "loot_collected": "{}",
            "active_monster_json": None,
            "supplies": {}
        }

    def _create_session(self, row_data=None):
        with patch('game_systems.adventure.adventure_session.AdventureRewards'), \
             patch('game_systems.adventure.adventure_session.CombatHandler'), \
             patch('game_systems.adventure.adventure_session.EventHandler'):
            return AdventureSession(
                self.mock_db,
                self.mock_qs,
                self.mock_im,
                self.discord_id,
                row_data=row_data
            )

    def test_init_malformed_json(self):
        """Test initialization with corrupted JSON fields."""
        bad_data = self.row_data.copy()
        bad_data["logs"] = "{bad"
        bad_data["loot_collected"] = "{bad"
        bad_data["active_monster_json"] = "{bad"

        session = self._create_session(bad_data)

        self.assertEqual(session.logs, [])
        self.assertEqual(session.loot, {})
        self.assertIsNone(session.active_monster)

    def test_calculate_fatigue_multiplier(self):
        """Test fatigue calculation."""
        session = self._create_session(self.row_data)

        # <= 16 steps
        session.steps_completed = 10
        self.assertEqual(session._calculate_fatigue_multiplier(), 1.0)

        # > 16 steps (20 steps = 4 excess = 5% bonus)
        session.steps_completed = 20
        self.assertAlmostEqual(session._calculate_fatigue_multiplier(), 1.05)

        # With Hardtack (20% reduction of bonus)
        session.supplies = {"hardtack": 1}
        # Bonus is 0.05 * 0.8 = 0.04 -> 1.04
        self.assertAlmostEqual(session._calculate_fatigue_multiplier(), 1.04)

    def test_fetch_session_context_error(self):
        """Test error handling in _fetch_session_context."""
        session = self._create_session(self.row_data)
        self.mock_db.get_combat_context_bundle.side_effect = Exception("DB Error")

        context = session._fetch_session_context()
        self.assertIsNone(context)

    def test_check_auto_condition_edge_cases(self):
        """Test _check_auto_condition with missing data."""
        session = self._create_session(self.row_data)

        # No active monster
        session.active_monster = None
        self.assertFalse(session._check_auto_condition({}))

        # Boss monster
        session.active_monster = {"tier": "Boss"}
        self.assertFalse(session._check_auto_condition({}))

        # Normal monster, but missing context vitals
        session.active_monster = {"tier": "Normal"}
        self.assertFalse(session._check_auto_condition({"vitals": None}))

        # Exception during calculation (e.g. division by zero if max_hp is 0, though max(1) prevents it)
        # We can force an error by making context["vitals"] a string or something unexpected
        self.assertFalse(session._check_auto_condition({"vitals": "invalid"}))

    @patch('game_systems.adventure.adventure_session.random.random')
    def test_apply_environmental_effects(self, mock_random):
        """Test environmental hazard application."""
        session = self._create_session(self.row_data)
        mock_random.return_value = 0.01 # Always trigger

        # Mock context
        stats = MagicMock()
        stats.max_hp = 100
        stats.max_mp = 50
        context = {
            "vitals": {"current_hp": 100, "current_mp": 50},
            "player_stats": stats,
            "stats_dict": {"HP": 100, "MP": 50}
        }

        # Blizzard
        session._apply_environmental_effects(context, Weather.BLIZZARD)
        self.assertLess(context["vitals"]["current_hp"], 100)
        self.assertIn("Freezing Winds", session.logs[-1])

        # Reset
        context["vitals"]["current_hp"] = 100
        session.logs = []

        # Sandstorm
        session._apply_environmental_effects(context, Weather.SANDSTORM)
        self.assertIn("Scouring Sand", session.logs[-1])

    def test_simulate_step_unknown_location(self):
        """Test simulate_step with invalid location."""
        session = self._create_session(self.row_data)
        session.location_id = "unknown_loc"

        result = session.simulate_step()
        self.assertTrue(result["dead"])
        self.assertIn("Error: Unknown location", result["sequence"][0][0])

    def test_simulate_step_context_fail(self):
        """Test simulate_step when context fetch fails."""
        session = self._create_session(self.row_data)
        # Mock LOCATIONS with content so it's truthy
        with patch('game_systems.adventure.adventure_session.LOCATIONS', {"forest": {"name": "Forest"}}):
            with patch.object(session, '_fetch_session_context', return_value=None):
                result = session.simulate_step()
                self.assertFalse(result["dead"]) # Not dead, just error
                self.assertIn("Error: Failed to load player data", result["sequence"][0][0])

    def test_attempt_flee_invalid_state(self):
        """Test _attempt_flee when state is invalid."""
        session = self._create_session(self.row_data)
        session.active_monster = None

        result = session._attempt_flee({})
        self.assertIn("Error: Invalid flee state", result["sequence"][0][0])

    def test_save_state_error(self):
        """Test save_state exception handling."""
        session = self._create_session(self.row_data)
        session.active = True
        self.mock_db.update_adventure_session.side_effect = Exception("Save Error")

        with self.assertRaises(Exception):
            session.save_state()

    def test_try_auto_potion(self):
        """Test _try_auto_potion logic."""
        session = self._create_session(self.row_data)

        context = {"vitals": {"current_hp": 10, "current_mp": 10}}
        max_hp = 100

        # No potion
        session.supplies = {}
        result = session._try_auto_potion(context, max_hp)
        self.assertIsNone(result)

        # With potion
        session.supplies = {"hp_potion_1": 1}

        # Mock CONSUMABLES
        mock_consumables = {"hp_potion_1": {"name": "Potion", "type": "hp", "effect": {"heal": 50}}}

        with patch('game_systems.adventure.adventure_session.CONSUMABLES', mock_consumables):
            result = session._try_auto_potion(context, max_hp)

            self.assertIsNotNone(result)
            self.assertEqual(context["vitals"]["current_hp"], 60) # 10 + 50
            self.assertIn("Auto-Potion", result)
            self.assertEqual(session.supplies.get("hp_potion_1"), None) # Consumed

    def test_check_auto_condition_fallback_hp(self):
        """Test _check_auto_condition when stats_dict is missing."""
        session = self._create_session(self.row_data)
        session.active_monster = {"tier": "Normal"}

        # stats_dict missing, should use player_stats.max_hp
        stats = MagicMock()
        stats.max_hp = 100
        context = {
            "vitals": {"current_hp": 20}, # 20%, should be < 30%
            "player_stats": stats
            # No stats_dict
        }

        # (20 / 100) < 0.30 -> Should be False?
        # _check_auto_condition returns True if >= 0.30 (safe to auto)
        # Returns False if < 0.30 (manual only)

        self.assertFalse(session._check_auto_condition(context))

        context["vitals"]["current_hp"] = 50
        self.assertTrue(session._check_auto_condition(context))
