"""
combat_phrases.py

Provides narrative text for combat events.
Exposes 'CombatPhrases' class for CombatEngine.
"""

import random

class CombatPhrases:
    @staticmethod
    def opening(monster_data):
        name = monster_data.get("name", "Enemy")
        return f"⚔️ **A wild {name} appears!** The air grows tense."

    @staticmethod
    def player_attack(player, monster, damage, is_crit):
        crit_text = " **(CRITICAL!)**" if is_crit else ""
        return f"🗡️ You strike the **{monster['name']}** for `{damage}` damage!{crit_text}"

    @staticmethod
    def monster_attack(monster, player, damage, is_crit):
        crit_text = " **(CRITICAL!)**" if is_crit else ""
        return f"💥 The **{monster['name']}** attacks! You take `{damage}` damage.{crit_text}"

    @staticmethod
    def monster_skill(monster, player, skill_data, damage, is_crit):
        skill_name = skill_data.get("name", "Special Attack")
        return f"🔥 **{monster['name']}** uses **{skill_name}**! You take `{damage}` damage!"

    @staticmethod
    def monster_buff(monster, buff_data):
        return f"✨ **{monster['name']}** grows stronger!"

    @staticmethod
    def player_victory(monster, exp, gold, leveled_up):
        msg = f"🏆 **Victory!** You defeated the {monster['name']}.\n" \
              f"✨ Gained `{exp} EXP`\n" \
              f"💰 Found `{gold} Gold`"
        if leveled_up:
            msg += "\n🌟 **LEVEL UP!** You feel stronger."
        return msg

    @staticmethod
    def player_defeated(monster):
        return f"💀 **Defeat...** The {monster['name']} was too strong. You black out..."