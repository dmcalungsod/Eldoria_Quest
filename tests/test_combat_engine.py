import pytest
from unittest.mock import MagicMock, patch
from game_systems.combat.combat_engine import CombatEngine


@pytest.fixture
def mock_player():
    player = MagicMock()
    # Mock LevelUpSystem wrapper interface
    player.level = 5
    player.hp_current = 100
    player.stats = MagicMock()
    player.stats.max_hp = 100
    player.stats.max_mp = 50
    player.stats.get_total_stats_dict.return_value = {
        "STR": 10,
        "END": 10,
        "DEX": 10,
        "AGI": 10,
        "MAG": 10,
        "LCK": 10,
        "HP": 100,
        "MP": 50,
    }
    player.is_stunned = False
    return player


@pytest.fixture
def mock_monster():
    return {
        "name": "Test Goblin",
        "HP": 50,
        "max_hp": 50,
        "ATK": 10,
        "DEF": 5,
        "MP": 0,
        "level": 5,
        "drops": [],
    }


def test_recoil_damage(mock_player, mock_monster):
    # Mock skill with 10% recoil
    skill = {
        "key_id": "reckless_swing",
        "name": "Reckless Swing",
        "type": "Active",
        "mp_cost": 0,
        "power_multiplier": 1.0,
        "self_damage_percent": 0.1,
        "scaling_stat": "STR",
    }

    # Patch DamageFormula to return fixed damage
    with patch(
        "game_systems.combat.combat_engine.DamageFormula.player_skill"
    ) as mock_calc:
        mock_calc.return_value = (50, False, "hit")  # 50 damage

        engine = CombatEngine(
            player=mock_player,
            monster=mock_monster,
            player_skills=[skill],
            player_mp=10,
            player_class_id=1,
            stats_dict=mock_player.stats.get_total_stats_dict(),
        )

        # Patch random to always use this skill
        with patch.object(
            engine,
            "_decide_player_skill",
            return_value={"skill": skill, "reason": "Test"},
        ):
            engine.run_combat_turn()

            # Expected Recoil: 10% of 50 = 5 damage
            # Player started with 100, should be 95
            assert engine.player_hp == 95


def test_bloodlust_heal(mock_player, mock_monster):
    # Mock bloodlust passive
    skills = [
        {
            "key_id": "bloodlust",
            "type": "Passive",
            "passive_bonus": {"kill_heal_percent": 0.05},
        }
    ]

    # Monster has 1 HP, guaranteed kill
    mock_monster["HP"] = 1
    mock_player.hp_current = 50  # Damaged player

    with patch(
        "game_systems.combat.combat_engine.DamageFormula.player_attack"
    ) as mock_calc:
        mock_calc.return_value = (10, False, "hit")

        engine = CombatEngine(
            player=mock_player,
            monster=mock_monster,
            player_skills=skills,
            player_mp=10,
            player_class_id=1,
            stats_dict=mock_player.stats.get_total_stats_dict(),
        )

        engine.run_combat_turn()

        # Expected Heal: 5% of 100 Max HP = 5 HP
        # Started at 50, should be 55
        assert engine.player_hp == 55


def test_status_immunity(mock_player, mock_monster):
    # Grant immunity via buff
    active_buffs = [{"stat": "immunity_stun", "amount": 1}]

    # Monster skill that stuns
    monster_skill = {
        "name": "Stun Bash",
        "power": 1.0,
        "status_effect": {"stun_chance": 1.0},  # 100% chance
    }

    # Force monster to use skill
    with patch(
        "game_systems.monsters.monster_actions.MonsterAI.choose_action",
        return_value={"type": "skill", "skill": monster_skill},
    ):
        # Force player to miss/do nothing to ensure monster turn happens
        with patch(
            "game_systems.combat.combat_engine.DamageFormula.player_attack",
            return_value=(0, False, "miss"),
        ):

            engine = CombatEngine(
                player=mock_player,
                monster=mock_monster,
                player_skills=[],
                player_mp=10,
                player_class_id=1,
                active_buffs=active_buffs,
                stats_dict=mock_player.stats.get_total_stats_dict(),
            )

            engine.run_combat_turn()

            # Verify player was NOT stunned
            assert not engine.player_stunned
            assert "🛡️ **Immune!**" in str(engine.run_combat_turn()["phrases"])


def test_negative_stat_debuff(mock_player, mock_monster):
    # Skill applying negative defense
    skill = {
        "key_id": "vitriol_bomb",
        "name": "Vitriol Bomb",
        "type": "Active",
        "mp_cost": 0,
        "debuff": {"DEF_percent": -0.1, "duration": 3},
        "power_multiplier": 1.0,
    }

    engine = CombatEngine(
        player=mock_player,
        monster=mock_monster,
        player_skills=[skill],
        player_mp=10,
        player_class_id=6,  # Alchemist
        stats_dict=mock_player.stats.get_total_stats_dict(),
    )

    with patch.object(
        engine,
        "_decide_player_skill",
        return_value={"skill": skill, "reason": "Test"},
    ):
        result = engine.run_combat_turn()

        # Check if debuff was applied to monster data in result
        # In engine, self.monster is modified.
        assert len(engine.monster["debuffs"]) > 0
        assert engine.monster["debuffs"][0]["DEF_percent"] == -0.1
        # Explicitly consume result to satisfy linter (F841)
        assert result is not None
