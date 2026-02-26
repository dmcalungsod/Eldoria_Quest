import os
import sys
import unittest
from unittest.mock import patch

# Add repo root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game_systems.monsters.monster_actions import MonsterAI


class TestMonsterActions(unittest.TestCase):
    def setUp(self):
        self.monster = {"name": "Test Monster", "max_hp": 100, "tier": "Normal", "skills": []}

    def test_choose_action_charged_skill(self):
        self.monster["charged_skill"] = {"name": "Big Boom"}
        action = MonsterAI.choose_action(self.monster, 50, 10)
        self.assertEqual(action["type"], "execute_charge")
        self.assertEqual(action["skill"]["name"], "Big Boom")

    def test_choose_action_heal_priority(self):
        # HP < 40% (30/100)
        # Has heal skill
        heal_skill = {"name": "Heal", "heal_power": 50, "mp_cost": 5}
        self.monster["skills"] = [heal_skill]

        # Patch random to ensure heal trigger (chance <= 70)
        with patch("random.randint", return_value=50):
            action = MonsterAI.choose_action(self.monster, 30, 10)
            self.assertEqual(action["type"], "skill")
            self.assertEqual(action["skill"]["name"], "Heal")

    def test_choose_action_heal_insufficient_mp(self):
        # HP < 40%, but not enough MP
        heal_skill = {"name": "Heal", "heal_power": 50, "mp_cost": 20}
        self.monster["skills"] = [heal_skill]

        with patch("random.randint", return_value=50):
            action = MonsterAI.choose_action(self.monster, 30, 10)
            # Should fall through to attack because heal is not usable
            self.assertEqual(action["type"], "attack")

    def test_choose_action_offensive_skill(self):
        # Full HP, has offensive skill
        off_skill = {"name": "Slash", "power": 1.2, "mp_cost": 5}
        self.monster["skills"] = [off_skill]

        # Patch random:
        # 1. Healing check skipped (HP high)
        # 2. Skill chance check (chance <= 30 for Normal) -> force success
        with patch("random.randint", return_value=10):
            with patch("random.choice", return_value=off_skill):
                action = MonsterAI.choose_action(self.monster, 100, 10)
                self.assertEqual(action["type"], "skill")
                self.assertEqual(action["skill"]["name"], "Slash")

    def test_choose_action_telegraph_high_power(self):
        # High power skill -> should telegraph
        nuke_skill = {"name": "Nuke", "power": 2.0, "mp_cost": 5}
        self.monster["skills"] = [nuke_skill]

        with patch("random.randint", return_value=10):  # Trigger skill usage
            with patch("random.choice", return_value=nuke_skill):
                action = MonsterAI.choose_action(self.monster, 100, 10)
                self.assertEqual(action["type"], "telegraph")
                self.assertEqual(action["skill"]["name"], "Nuke")

    def test_choose_action_buff_logic(self):
        # Only buff skill available
        buff_skill = {"name": "Rage", "buff_data": {"stat": "ATK"}, "mp_cost": 5}
        self.monster["skills"] = [buff_skill]

        # Patch random to fail skill chance (so it falls to buff)
        # Skill chance is checked for OFFENSIVE skills only in step 2.
        # Step 3 is Buff logic.

        # Logic review:
        # 2. Offensive Skill Logic: filters heal_power==0 AND no buff_data.
        # So buff_skills are NOT in offensive_skills list.
        # So step 2 is skipped if only buff skills exist.

        # Step 3: Buff Logic. 25% chance.
        with patch("random.randint", return_value=10):  # <= 25
            with patch("random.choice", return_value=buff_skill):
                action = MonsterAI.choose_action(self.monster, 100, 10)
                self.assertEqual(action["type"], "buff")
                self.assertEqual(action["buff"]["name"], "Rage")

    def test_choose_action_fallback_attack(self):
        # No skills
        self.monster["skills"] = []
        action = MonsterAI.choose_action(self.monster, 100, 10)
        self.assertEqual(action["type"], "attack")

    def test_apply_buff(self):
        buff_skill = {"name": "Rage", "buff_data": {"stat": "ATK", "multiplier": 1.5, "duration": 3}}
        self.monster["ATK"] = 10

        MonsterAI.apply_buff(self.monster, buff_skill)

        self.assertEqual(self.monster["ATK"], 15)  # 10 * 1.5
        self.assertEqual(len(self.monster["buffs"]), 1)
        self.assertEqual(self.monster["buffs"][0]["increase"], 5)

    def test_handle_buffs_expiration(self):
        self.monster["ATK"] = 15
        self.monster["buffs"] = [{"stat": "ATK", "increase": 5, "duration": 1, "name": "Rage"}]

        msgs = MonsterAI.handle_buffs(self.monster)

        self.assertEqual(self.monster["ATK"], 10)  # Reverted
        self.assertEqual(len(self.monster["buffs"]), 0)
        self.assertEqual(len(msgs), 1)
        self.assertIn("wore off", msgs[0])

    def test_handle_buffs_decrement(self):
        self.monster["ATK"] = 15
        self.monster["buffs"] = [{"stat": "ATK", "increase": 5, "duration": 2, "name": "Rage"}]

        msgs = MonsterAI.handle_buffs(self.monster)

        self.assertEqual(self.monster["ATK"], 15)  # Still active
        self.assertEqual(len(self.monster["buffs"]), 1)
        self.assertEqual(self.monster["buffs"][0]["duration"], 1)
        self.assertEqual(len(msgs), 0)


if __name__ == "__main__":
    unittest.main()
