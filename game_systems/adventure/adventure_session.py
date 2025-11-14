"""
adventure_session.py

Represents a single active adventure session.
Handles the simulation of combat steps and log generation.
"""

import json
import random
import datetime
from game_systems.combat.combat_engine import CombatEngine
from game_systems.data.monsters import MONSTERS
from game_systems.data.adventure_locations import LOCATIONS
from game_systems.player.player_stats import PlayerStats
from game_systems.player.level_up import LevelUpSystem
import game_systems.data.emojis as E

class AdventureSession:
    def __init__(self, db_manager, discord_id, row_data=None):
        self.db = db_manager
        self.discord_id = discord_id
        
        if row_data:
            self.location_id = row_data['location_id']
            self.end_time = datetime.datetime.fromisoformat(row_data['end_time'])
            self.logs = json.loads(row_data['logs'])
            self.loot = json.loads(row_data['loot_collected'])
            self.active = bool(row_data['active'])
        else:
            # Initialize new (handled by manager mostly)
            self.active = False

    async def simulate_step(self):
        """
        Simulates one 'step' (e.g., 5 minutes interval).
        Determines if a fight happens, resolves it, and updates logs.
        """
        location = LOCATIONS.get(self.location_id)
        if not location:
            return

        # 1. Fetch Player Stats
        stats_json = self.db.get_player_stats_json(self.discord_id)
        player_stats = PlayerStats.from_dict(stats_json)
        
        # Load basic player info for level scaling reference
        conn = self.db.connect()
        cur = conn.cursor()
        cur.execute("SELECT level, experience, exp_to_next, gold FROM players WHERE discord_id = ?", (self.discord_id,))
        p_row = cur.fetchone()
        conn.close()

        # Wrapper for CombatEngine
        player_wrapper = LevelUpSystem(player_stats, p_row['level'], p_row['experience'], p_row['exp_to_next'])

        # 2. Pick a Monster
        monster_pool = location['monsters']
        # Weighted random choice
        choices, weights = zip(*monster_pool)
        monster_key = random.choices(choices, weights=weights, k=1)[0]
        
        # Lookup monster data (Clone it so we don't modify the template)
        monster_template = MONSTERS.get(monster_key)
        if not monster_template:
            return 
        
        # Create a combat-ready monster dict (renaming keys for CombatEngine compatibility if needed)
        monster_instance = {
            "name": monster_template["name"],
            "level": monster_template["level"],
            "HP": monster_template["hp"],
            "MP": 10, # Default MP for simple mobs
            "ATK": monster_instance_atk(monster_template),
            "DEF": monster_template["def"],
            "CON": monster_template["hp"] // 5, # Approx
            "DEX": monster_template["level"], 
            "INT": 1,
            "xp": monster_template["xp"],
            "gold_drop": monster_template["level"] * 2, # Basic calculation
            "drops": monster_template.get("drops", [])
        }

        # 3. Resolve Combat
        engine = CombatEngine(player_wrapper, monster_instance)
        result = engine.begin_combat()

        # 4. Process Results
        timestamp = datetime.datetime.now().strftime("%H:%M")
        
        if result['winner'] == 'player':
            # Add Loot
            loot_text = []
            # Gold
            self.add_loot("gold", result['gold'])
            loot_text.append(f"{result['gold']} Gold")
            
            # EXP (Note: Actual EXP apply happens at END of adventure to prevent leveling mid-dungeon)
            self.add_loot("exp", result['exp'])
            loot_text.append(f"{result['exp']} EXP")

            # Monster Drops
            for drop_name, chance in monster_instance['drops']:
                if random.randint(1, 100) <= chance:
                    # Map drop keys to readable names if needed, for now use keys
                    self.add_loot(drop_name, 1)
                    loot_text.append(f"{drop_name}")

            log_entry = (
                f"`[{timestamp}]` ⚔️ **Encounter:** {monster_instance['name']}\n"
                f"> Defeated! Gained: {', '.join(loot_text)}.\n"
                f"> *HP remaining: {player_stats.max_hp}* (Auto-heal)" # For idle, we often auto-heal or track persistent HP. 
                # Note: For simple Idle, we assume full heal between fights unless we add persistent HP tracking.
            )
        else:
            # Player Died
            log_entry = (
                f"`[{timestamp}]` 💀 **Defeat:** Overwhelmed by {monster_instance['name']}.\n"
                f"> The Guild sends a rescue party. Adventure ends early."
            )
            self.active = False # End session immediately

        # 5. Save Log
        self.logs.append(log_entry)
        self.save_state()
        return self.active

    def add_loot(self, key, amount):
        if key in self.loot:
            self.loot[key] += amount
        else:
            self.loot[key] = amount

    def save_state(self):
        conn = self.db.connect()
        cur = conn.cursor()
        cur.execute("""
            UPDATE adventure_sessions 
            SET logs = ?, loot_collected = ?, active = ?
            WHERE discord_id = ?
        """, (json.dumps(self.logs), json.dumps(self.loot), 1 if self.active else 0, self.discord_id))
        conn.commit()
        conn.close()

def monster_instance_atk(template):
    # Helper to extract attack from template
    return template.get("atk", 10)