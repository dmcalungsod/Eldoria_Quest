"""
adventure_manager.py

Orchestrates all active adventures.
- Starts new sessions
- Checks for completion
- Triggers the 5-minute update steps
"""

import sqlite3
import json
import datetime
from discord.ext import tasks
from .adventure_session import AdventureSession
from game_systems.guild_system.reward_system import RewardSystem # To finalize rewards
from game_systems.data.materials import MATERIALS

class AdventureManager:
    def __init__(self, db_manager, bot):
        self.db = db_manager
        self.bot = bot
        # Start the background loop
        self.update_loop.start()

    def start_adventure(self, discord_id: int, location_id: str, duration_minutes: int):
        """
        Begins a new adventure session in the DB.
        """
        start_time = datetime.datetime.now()
        end_time = start_time + datetime.timedelta(minutes=duration_minutes)
        
        conn = self.db.connect()
        cur = conn.cursor()
        
        # Clear old sessions
        cur.execute("DELETE FROM adventure_sessions WHERE discord_id = ?", (discord_id,))
        
        cur.execute("""
            INSERT INTO adventure_sessions 
            (discord_id, location_id, start_time, end_time, duration_minutes, active, logs, loot_collected)
            VALUES (?, ?, ?, ?, ?, 1, '[]', '{}')
        """, (discord_id, location_id, start_time.isoformat(), end_time.isoformat(), duration_minutes))
        
        conn.commit()
        conn.close()
        return True

    def get_active_session(self, discord_id):
        conn = self.db.connect()
        cur = conn.cursor()
        cur.execute("SELECT * FROM adventure_sessions WHERE discord_id = ?", (discord_id,))
        row = cur.fetchone()
        conn.close()
        return row

    @tasks.loop(minutes=5)
    async def update_loop(self):
        """
        Runs every 5 minutes.
        1. Checks all active sessions.
        2. Triggers a simulation step (fight).
        3. Checks if time is up.
        """
        # In a production bot, we wouldn't fetch ALL, but batch them. 
        # For now, fetching all is fine.
        conn = self.db.connect()
        cur = conn.cursor()
        cur.execute("SELECT * FROM adventure_sessions WHERE active = 1")
        active_rows = cur.fetchall()
        conn.close()

        for row in active_rows:
            session = AdventureSession(self.db, row['discord_id'], row)
            
            # check if time expired
            now = datetime.datetime.now()
            if now >= session.end_time:
                await self.complete_adventure(session)
                continue

            # Simulate step
            is_alive = await session.simulate_step()
            
            if not is_alive:
                # Player died in combat
                await self.fail_adventure(session)

    async def complete_adventure(self, session: AdventureSession):
        """
        Finalizes the adventure, grants rewards, and notifies the user.
        """
        # 1. Calculate Totals
        total_gold = session.loot.pop("gold", 0)
        total_exp = session.loot.pop("exp", 0)
        
        # 2. Grant Rewards to DB
        conn = self.db.connect()
        cur = conn.cursor()
        
        # Gold
        cur.execute("UPDATE players SET gold = gold + ? WHERE discord_id = ?", (total_gold, session.discord_id))
        
        # EXP (Using simple SQL update here, ideally use LevelUpSystem if we want level up checks)
        # For simplicity in the loop:
        cur.execute("UPDATE players SET experience = experience + ? WHERE discord_id = ?", (total_exp, session.discord_id))
        
        # Items (Materials)
        # We need to map drop keys (e.g. 'goblin_ear') to Inventory
        for item_key, count in session.loot.items():
            # Look up display name in MATERIALS
            mat_data = MATERIALS.get(item_key)
            item_name = mat_data['name'] if mat_data else item_key
            item_type = "material"
            
            # Add to inventory table
            # Check existence
            cur.execute("SELECT count FROM inventory WHERE discord_id=? AND item_name=?", (session.discord_id, item_name))
            inv_row = cur.fetchone()
            if inv_row:
                cur.execute("UPDATE inventory SET count = count + ? WHERE discord_id=? AND item_name=?", (count, session.discord_id, item_name))
            else:
                cur.execute("INSERT INTO inventory (discord_id, item_name, item_type, count) VALUES (?, ?, ?, ?)", (session.discord_id, item_name, item_type, count))

        # Mark session inactive
        cur.execute("UPDATE adventure_sessions SET active = 0 WHERE discord_id = ?", (session.discord_id,))
        conn.commit()
        conn.close()

        # 3. Notify User (DM or specific channel)
        user = self.bot.get_user(session.discord_id)
        if user:
            summary = f"🌲 **Adventure Complete!**\nDuration: {session.logs[-1] if session.logs else 'Unknown'}\n"
            summary += f"💰 +{total_gold} Gold\n✨ +{total_exp} EXP\n📦 Items: {', '.join(f'{k} x{v}' for k,v in session.loot.items())}"
            try:
                await user.send(summary)
            except:
                pass # Can't DM

    async def fail_adventure(self, session: AdventureSession):
        # Handle death (partial rewards or zero rewards)
        conn = self.db.connect()
        cur = conn.cursor()
        cur.execute("UPDATE adventure_sessions SET active = 0 WHERE discord_id = ?", (session.discord_id,))
        conn.commit()
        conn.close()
        
        user = self.bot.get_user(session.discord_id)
        if user:
            try:
                await user.send("💀 **Adventure Failed**\nYou were defeated in the wilds. The Guild rescue team has brought you back.")
            except:
                pass

    @update_loop.before_loop
    async def before_loop(self):
        await self.bot.wait_until_ready()