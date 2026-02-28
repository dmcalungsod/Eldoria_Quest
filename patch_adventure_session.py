import re

with open("game_systems/adventure/adventure_session.py") as f:
    content = f.read()

# Introduce helper method `_update_vitals_if_changed`
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
"""

if "_update_vitals_if_changed" not in content:
    content = content.replace("    def _process_auto_combat(", helper_code + "\n    def _process_auto_combat(")


# Patch _process_auto_combat
content = re.sub(
    r'        # Save final vitals via Delta[\s\S]*?self\.db\.update_player_vitals_delta\(self\.discord_id, delta_hp, delta_mp, max_hp, max_mp\)',
    r'''        # Final Results Block
        final_block = []
        if player_won:
            final_block.append(
                f"\\n⚔️ **Victory:** Defeated {result['monster_data']['name']} in {len(turn_reports)} rounds."
            )

            # Grant Rewards
            reward_texts = self.rewards.process_victory(
                battle_report=report,
                report_list=turn_reports,
                combat_result=result,
                quest_system=self.quest_system,
                inventory_manager=self.inventory_manager,
                session_loot=self.loot,
                location_id=self.location_id,
            )
            final_block.extend(reward_texts)

        elif is_dead:
            final_block.append("\\n💀 **You have been defeated.**")

        if final_block:
            sequence.append(final_block)

        # Add to master log
        for frame in sequence:
            self.logs.extend(frame)

        if persist:
            self.save_state()
            self._update_vitals_if_changed(context, initial_hp, initial_mp)''',
    content
)

# Patch _process_combat_turn
content = re.sub(
    r'            # Update vitals only after successful save\s+if context:\s+final_hp = context\["vitals"\]\["current_hp"\][\s\S]*?self\.db\.update_player_vitals_delta\(self\.discord_id, delta_hp, delta_mp, max_hp, max_mp\)',
    r'''            # Update vitals only after successful save
            self._update_vitals_if_changed(context, initial_hp, initial_mp)''',
    content
)

with open("game_systems/adventure/adventure_session.py", "w") as f:
    f.write(content)
