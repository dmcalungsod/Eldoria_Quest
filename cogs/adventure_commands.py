"""
adventure_commands.py

Slash commands for the Idle Adventure System.
Allows players to:
- /adventure start: Pick a zone and duration.
- /adventure status: Check live logs of the current trip.
"""

import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Select, Button
from database.database_manager import DatabaseManager
from game_systems.adventure.adventure_manager import AdventureManager
from game_systems.data.adventure_locations import LOCATIONS
import game_systems.data.emojis as E

class AdventureCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = DatabaseManager()
        self.manager = AdventureManager(self.db, bot) # Starts the loop

    @app_commands.command(name="adventure", description="Manage your expeditions.")
    @app_commands.choices(action=[
        app_commands.Choice(name="Start Expedition", value="start"),
        app_commands.Choice(name="Check Status", value="status"),
        app_commands.Choice(name="Return Early (Cancel)", value="cancel")
    ])
    async def adventure(self, interaction: discord.Interaction, action: str):
        discord_id = interaction.user.id
        active_session = self.manager.get_active_session(discord_id)

        if action == "status":
            if not active_session or not active_session['active']:
                await interaction.response.send_message("You are not currently on an adventure.", ephemeral=True)
                return
            
            # Show logs
            logs = eval(active_session['logs']) # stored as string
            loot = eval(active_session['loot_collected'])
            
            embed = discord.Embed(title=f"{E.QUEST_SCROLL} Adventure Log", color=discord.Color.green())
            embed.description = "**Latest Events:**\n" + ("\n".join(logs[-5:]) if logs else "The journey begins...")
            
            loot_str = ", ".join([f"{k} x{v}" for k,v in loot.items()])
            embed.add_field(name="Backpack", value=loot_str if loot_str else "Empty")
            
            await interaction.response.send_message(embed=embed, ephemeral=True)

        elif action == "start":
            if active_session and active_session['active']:
                await interaction.response.send_message("You are already on an adventure! Use `/adventure status`.", ephemeral=True)
                return
            
            # Show Location Select Menu
            view = AdventureSetupView(self.db, self.manager)
            await interaction.response.send_message(f"{E.MAP} **Select a Destination:**", view=view, ephemeral=True)

        elif action == "cancel":
            # Implement cancel logic (mark active=0, maybe give partial rewards)
            await interaction.response.send_message("You signal for extraction. (Implementation pending)", ephemeral=True)

class AdventureSetupView(View):
    def __init__(self, db, manager):
        super().__init__()
        self.db = db
        self.manager = manager
        
        # Location Select
        self.location_select = Select(placeholder="Choose a Zone...")
        for key, loc in LOCATIONS.items():
            # Use the emoji from the location data file
            self.location_select.add_option(
                label=loc['name'], 
                value=key, 
                description=f"Lv. {loc['level_req']} | {loc['min_rank']}-Rank",
                emoji=loc.get('emoji') # Use .get() for safety
            )
        self.location_select.callback = self.location_callback
        self.add_item(self.location_select)

    async def location_callback(self, interaction: discord.Interaction):
        loc_id = self.location_select.values[0]
        loc_data = LOCATIONS[loc_id]
        
        # Create Duration Buttons
        self.clear_items()
        
        for mins in loc_data['duration_options']:
            btn = Button(label=f"{mins} Mins", style=discord.ButtonStyle.primary, custom_id=f"dur_{loc_id}_{mins}")
            btn.callback = self.duration_callback
            self.add_item(btn)
            
        await interaction.response.edit_message(
            content=f"{loc_data.get('emoji', E.MAP)} **Destination:** {loc_data['name']}\nSelect Duration:", 
            view=self
        )

    async def duration_callback(self, interaction: discord.Interaction):
        # custom_id format: dur_locationID_minutes
        parts = interaction.data['custom_id'].split('_')
        loc_id = "_".join(parts[1:-1]) # handle IDs with underscores
        duration = int(parts[-1])
        
        self.manager.start_adventure(interaction.user.id, loc_id, duration)
        await interaction.response.edit_message(
            content=f"{E.CHECK} **Adventure Started!**\n"
                    f"You have set off for **{LOCATIONS[loc_id]['name']}** for {duration} minutes.\n"
                    f"Check back with `/adventure status`.", 
            view=None
        )

async def setup(bot):
    await bot.add_cog(AdventureCommands(bot))