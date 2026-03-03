from unittest.mock import MagicMock, patch

import pytest

from game_systems.combat.combat_engine import CombatEngine
from game_systems.data.skills_data import SKILLS
from game_systems.player.player_stats import PlayerStats


class TestWarriorExpansion:
    @pytest.fixture
    def setup_combat(self):
        """Sets up a basic combat scenario with a Warrior player."""
        # Mock Player
        player = MagicMock()
        player.name = "TestWarrior"
        player.level = 10
        player.hp_current = 500
        player.stats = MagicMock(spec=PlayerStats)
        player.stats.max_hp = 500
        player.stats.get_total_stats_dict.return_value = {
            "HP": 500,
            "MP": 100,
            "STR": 50,
            "END": 50,
            "DEX": 20,
            "AGI": 20,
            "MAG": 10,
            "LCK": 10,
        }
        player.add_exp = MagicMock()
        # Default stun state
        player.is_stunned = False
        player.is_silenced = False

        # Mock Monster
        monster = {
            "name": "Target Dummy",
            "HP": 1000,
            "max_hp": 1000,
            "ATK": 50,
            "DEF": 20,
            "level": 10,
            "tier": "Normal",
            "drops": [],
        }

        # Warrior Skills - Focusing only on implemented/verified mechanics (Stun/Immunity)
        warrior_skills = [SKILLS["shield_bash"], SKILLS["unstoppable_force"]]

        return player, monster, warrior_skills

    def test_shield_bash_stun(self, setup_combat):
        """Test that Shield Bash has a chance to stun."""
        player, monster, skills = setup_combat

        # Force stun chance to 100% via patching random
        with patch("random.random", return_value=0.0):  # 0.0 < 0.3
            engine = CombatEngine(
                player=player,
                monster=monster,
                player_skills=skills,
                player_mp=100,
                player_class_id=1,
                action="skill:shield_bash",
            )
            result = engine.run_combat_turn()

            # Verify Stun message
            stun_msg_present = any("Stunned!" in phrase for phrase in result["phrases"])
            assert stun_msg_present, "Combat log should mention Stun."

            # Verify monster lost turn (log shows skip)
            monster_skip_msg = any("reeling and misses its turn" in phrase for phrase in result["phrases"])
            assert monster_skip_msg, "Monster should skip turn when stunned."

    def test_unstoppable_force_buff(self, setup_combat):
        """Test Unstoppable Force applies buffs and immunity."""
        player, monster, skills = setup_combat

        engine = CombatEngine(
            player=player,
            monster=monster,
            player_skills=skills,
            player_mp=100,
            player_class_id=1,
            action="skill:unstoppable_force",
        )

        result = engine.run_combat_turn()

        # Check new_buffs in result
        new_buffs = result["new_buffs"]

        # Expect ATK, DEF, immunity_stun
        buff_names = [b["stat"] for b in new_buffs]

        assert "ATK" in buff_names, "Should have ATK buff."
        assert "DEF" in buff_names, "Should have DEF buff."
        assert "immunity_stun" in buff_names, "Should have Stun Immunity."

    def test_immunity_prevents_status(self, setup_combat):
        """Test that having immunity prevents status application."""
        player, monster, skills = setup_combat

        # Setup: Player has immunity_stun
        active_buffs = [{"name": "Unstoppable", "stat": "immunity_stun", "amount": 1, "duration": 3}]

        # Initialize Engine
        engine = CombatEngine(
            player=player,
            monster=monster,
            player_skills=skills,
            player_mp=100,
            player_class_id=1,
            active_buffs=active_buffs,
            action="defend",  # Player defends
        )

        # Mock Monster Action to be a skill that stuns
        stun_skill = {
            "name": "Stunning Blow",
            "type": "physical",
            "power": 1.0,
            "status_effect": {"stun_chance": 1.0},  # 100% chance
        }

        # Force monster to use stun skill
        with patch("game_systems.monsters.monster_actions.MonsterAI.choose_action") as mock_ai:
            mock_ai.return_value = {"type": "skill", "skill": stun_skill}

            # Force random to hit stun (though chance is 1.0)
            with patch("random.random", return_value=0.0):
                # Run turn
                result = engine.run_combat_turn()

            # Verify "Immune!" message in log
            immune_msg_present = any("Immune!" in phrase for phrase in result["phrases"])
            assert immune_msg_present, "Combat log should mention Immunity."

            # Also verify NO "Stunned!" message and player_stunned is False
            stun_msg_present = any("You are reeling" in phrase for phrase in result["phrases"])
            assert not stun_msg_present, "Player should not be stunned."
            assert not engine.player_stunned, "Engine state should not be stunned."

    def test_player_stunned_mechanic(self, setup_combat):
        """Test that if player is stunned, they skip their turn."""
        player, monster, skills = setup_combat

        # Setup: Player IS stunned
        player.is_stunned = True

        engine = CombatEngine(
            player=player, monster=monster, player_skills=skills, player_mp=100, player_class_id=1, action="attack"
        )

        # Execute turn
        result = engine.run_combat_turn()

        # Verify Stun Message
        assert any("You cannot move!" in phrase for phrase in result["phrases"]), "Log should say player cannot move."

        # Verify Player did NOT attack (monster HP same)
        assert result["monster_hp"] == 1000, "Monster should not take damage."

        # Verify result reports stun cleared
        assert "player_stunned" in result
        assert result["player_stunned"] is False, "Stun should be consumed/cleared."
