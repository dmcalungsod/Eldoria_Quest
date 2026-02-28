
with open("game_systems/adventure/adventure_session.py") as f:
    content = f.read()

helper_code = """
    def _update_vitals_if_changed(self, context, initial_hp, initial_mp):
        if not context:
            return
        final_hp = context["vitals"]["current_hp"]
        final_mp = context["vitals"]["current_mp"]
        delta_hp = final_hp - initial_hp
        delta_mp = final_mp - initial_mp

        if delta_hp != 0 or delta_mp != 0:
            player_stats = context["player_stats"]
            stats_dict = context.get("stats_dict")
            max_hp = stats_dict.get("HP", player_stats.max_hp) if stats_dict else player_stats.max_hp
            max_mp = stats_dict.get("MP", player_stats.max_mp) if stats_dict else player_stats.max_mp
            self.db.update_player_vitals_delta(self.discord_id, delta_hp, delta_mp, max_hp, max_mp)

    def _resolve_auto_combat(
"""

content = content.replace("    def _resolve_auto_combat(", helper_code)

with open("game_systems/adventure/adventure_session.py", "w") as f:
    f.write(content)
