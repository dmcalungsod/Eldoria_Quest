import os
import sys
from unittest.mock import MagicMock, patch

# Add repo root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Mock dependencies before import
mock_pymongo = MagicMock()
mock_pymongo.errors = MagicMock()
sys.modules["pymongo"] = mock_pymongo
sys.modules["pymongo.errors"] = mock_pymongo.errors

sys.modules["discord"] = MagicMock()
sys.modules["discord.ext"] = MagicMock()

from game_systems.adventure.adventure_session import AdventureSession  # noqa: E402
from game_systems.combat.combat_engine import CombatEngine  # noqa: E402


class TestAdventureFatigue:
    def test_calculate_fatigue_multiplier(self):
        """
        Verify that _calculate_fatigue_multiplier returns correct values.
        Logic: > 16 steps -> +5% per 4 steps.
        """
        # We can mock AdventureSession to test just this method
        session = MagicMock(spec=AdventureSession)
        session.supplies = {}
        # Bind the method to the mock
        session._calculate_fatigue_multiplier = AdventureSession._calculate_fatigue_multiplier.__get__(
            session, AdventureSession
        )

        # Mock supplies (new requirement)
        session.supplies = {}

        # Case 1: Under threshold (1 hour = 4 steps)
        session.steps_completed = 4
        assert session._calculate_fatigue_multiplier() == 1.0

        # Case 2: At threshold (4 hours = 16 steps)
        session.steps_completed = 16
        assert session._calculate_fatigue_multiplier() == 1.0

        # Case 3: 5 hours (20 steps) -> +5%
        session.steps_completed = 20
        assert session._calculate_fatigue_multiplier() == 1.05

        # Case 4: 8 hours (32 steps) -> (16/4)*0.05 = 0.20 -> 1.20
        session.steps_completed = 32
        assert session._calculate_fatigue_multiplier() == 1.20

        # Case 5: 24 hours (96 steps) -> (80/4)*0.05 = 1.00 -> 2.00
        session.steps_completed = 96
        assert session._calculate_fatigue_multiplier() == 2.00

    @patch("game_systems.combat.combat_engine.DamageFormula")
    def test_combat_engine_applies_multiplier(self, mock_damage_formula):
        """
        Verify that CombatEngine applies monster_dmg_mult to monster damage.
        """
        # Setup Mocks
        player = MagicMock()
        player.stats.max_hp = 100
        player.hp_current = 100
        player.stats.get_total_stats_dict.return_value = {"HP": 100}

        monster = {"HP": 100, "ATK": 10, "DEF": 0, "name": "Test Mob"}
        skills = []

        # Mock DamageFormula return values (damage, crit, event_type)
        mock_damage_formula.monster_attack.return_value = (10, False, "hit")
        mock_damage_formula.monster_skill.return_value = (20, False, "hit")
        # Mock player attack to avoid crash during player turn
        mock_damage_formula.player_attack.return_value = (10, False, "hit")

        # Test 1: Normal Multiplier (1.0)
        engine = CombatEngine(
            player=player, monster=monster, player_skills=skills, player_mp=10, player_class_id=1, monster_dmg_mult=1.0
        )

        # Mock MonsterAI to force attack
        with patch("game_systems.monsters.monster_actions.MonsterAI.choose_action", return_value={"type": "attack"}):
            result = engine.run_combat_turn()

        # Verify damage taken = 10 (base) * 1.0
        assert result["turn_report"]["damage_taken"] == 10

        # Test 2: Fatigue Multiplier (1.5)
        engine_fatigued = CombatEngine(
            player=player, monster=monster, player_skills=skills, player_mp=10, player_class_id=1, monster_dmg_mult=1.5
        )

        with patch("game_systems.monsters.monster_actions.MonsterAI.choose_action", return_value={"type": "attack"}):
            result = engine_fatigued.run_combat_turn()

        # Verify damage taken = 10 (base) * 1.5 = 15
        assert result["turn_report"]["damage_taken"] == 15

        # Test 3: Skill Damage Multiplier
        with patch(
            "game_systems.monsters.monster_actions.MonsterAI.choose_action", return_value={"type": "skill", "skill": {}}
        ):
            result = engine_fatigued.run_combat_turn()

        # Verify damage taken = 20 (base skill) * 1.5 = 30
        assert result["turn_report"]["damage_taken"] == 30
