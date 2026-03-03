"""
cogs/event_cog.py

Discord Cog for the World Event System.
Handles scheduling, commands, and announcements for global events like "The Blood Moon".
"""

import datetime
import logging
import random

import discord
from discord import app_commands
from discord.ext import commands, tasks

import game_systems.data.emojis as E
from database.database_manager import DatabaseManager
from game_systems.core.world_time import WorldTime
from game_systems.events.world_event_system import WorldEventSystem

logger = logging.getLogger("eldoria.cogs.events")


class EventCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = DatabaseManager()
        self.system = WorldEventSystem(self.db)

        # Start the background task
        self.check_event_cycle.start()
        logger.info("EventCog initialized.")

    def cog_unload(self):
        self.check_event_cycle.cancel()

    @tasks.loop(hours=1)
    async def check_event_cycle(self):
        """
        Runs every hour to check event status.
        - Ends expired events.
        - Starts seasonal events.
        """
        try:
            # get_current_event automatically handles expiration
            active = self.system.get_current_event()

            # --- Seasonal Event Check ---
            if not active:
                now = WorldTime.now()

                # Grand Harvest Festival: Oct 1st - Oct 7th
                # Only auto-start on Oct 1st (to avoid spamming starts if manually ended)
                if now.month == 10 and now.day == 1 and now.hour == 12:
                    success = self.system.start_event(
                        WorldEventSystem.HARVEST_FESTIVAL, 24 * 7
                    )
                    if success:
                        config = self.system.EVENT_CONFIGS[
                            WorldEventSystem.HARVEST_FESTIVAL
                        ]
                        await self._announce(
                            f"🍂 **SEASONAL EVENT STARTED!** 🍂\n\n"
                            f"**{config['name']}**\n"
                            f"{config['description']}\n\n"
                            f"Gathering yields are doubled for the next week! 🌾"
                        )
                        logger.info("Auto-started Harvest Festival.")

                # Time Quake: Random Chance (2%)
                elif random.random() < 0.02:
                    success = self.system.start_event(WorldEventSystem.TIME_QUAKE, 24)
                    if success:
                        config = self.system.EVENT_CONFIGS[WorldEventSystem.TIME_QUAKE]
                        await self._announce(
                            f"⏳ **A TIME QUAKE HAS OCCURRED!** ⏳\n\n"
                            f"**{config['name']}**\n"
                            f"{config['description']}\n\n"
                            f"The Silent City of Ouros is stabilizing for the next 24 hours! 🕰️"
                        )
                        logger.info("Auto-started Time Quake.")

                # Mystic Merchant: Random Chance (2%)
                elif random.random() < 0.02:
                    success = self.system.start_event(
                        WorldEventSystem.MYSTIC_MERCHANT, 24
                    )
                    if success:
                        config = self.system.EVENT_CONFIGS[
                            WorldEventSystem.MYSTIC_MERCHANT
                        ]
                        await self._announce(
                            f"🔮 **THE MYSTIC MERCHANT ARRIVES!** 🔮\n\n"
                            f"**{config['name']}**\n"
                            f"{config['description']}\n\n"
                            f"Visit the **Guild Services** menu to find the **Mystic Merchant**! 🪙"
                        )
                        logger.info("Auto-started Mystic Merchant.")

        except Exception as e:
            logger.error(f"Error in event cycle: {e}", exc_info=True)

    @check_event_cycle.before_loop
    async def before_check_event_cycle(self):
        await self.bot.wait_until_ready()

    async def _announce(self, message: str):
        """Attempts to announce to a guild channel (guild-hall or general)."""
        for guild in self.bot.guilds:
            channel = discord.utils.get(guild.text_channels, name="guild-hall")
            if not channel:
                channel = discord.utils.get(guild.text_channels, name="general")

            if channel:
                try:
                    await channel.send(message)
                except Exception as e:
                    logger.error(f"Failed to announce in {guild.name}: {e}")

    # ==================================================================
    # USER COMMANDS
    # ==================================================================

    @app_commands.command(
        name="event_status", description="View the current active World Event."
    )
    async def event_status(self, interaction: discord.Interaction):
        """Displays the current world event status."""
        active = self.system.get_current_event()

        if not active:
            embed = discord.Embed(
                title="🌙 No Active Event",
                description="The world is calm. The skies are clear.",
                color=discord.Color.dark_grey(),
            )
            await interaction.response.defer(ephemeral=True)
            await interaction.edit_original_response(embed=embed)
            return

        end_time = datetime.datetime.fromisoformat(active["end_time"])
        time_remaining = end_time - WorldTime.now()
        days = time_remaining.days
        hours = time_remaining.seconds // 3600
        minutes = (time_remaining.seconds % 3600) // 60

        embed = discord.Embed(
            title=f"🌍 Active Event: {active['name']}",
            description=active["description"],
            color=discord.Color.red(),
        )
        embed.add_field(
            name="Ends In", value=f"{days}d {hours}h {minutes}m", inline=True
        )

        modifiers = []
        for key, val in active.get("modifiers", {}).items():
            name = key.replace("_", " ").title()
            val_str = f"x{val}" if val < 2.0 else f"x{val} 🔥"
            modifiers.append(f"• **{name}**: {val_str}")

        if modifiers:
            embed.add_field(
                name="Global Effects", value="\n".join(modifiers), inline=False
            )

        await interaction.response.defer(ephemeral=True)
        await interaction.edit_original_response(embed=embed)

    # ==================================================================
    # ADMIN COMMANDS
    # ==================================================================

    @app_commands.command(
        name="admin_event_start", description="[Admin] Manually start a world event."
    )
    @app_commands.describe(
        event_type="Type of event (blood_moon, celestial_convergence, void_incursion, elemental_surge)",
        hours="Duration in hours",
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def admin_start(
        self, interaction: discord.Interaction, event_type: str, hours: int = 24
    ):
        """Manually starts an event."""
        if event_type not in self.system.EVENT_CONFIGS:
            await interaction.response.defer(ephemeral=True)
            await interaction.edit_original_response(
                content=f"{E.ERROR} Invalid type. Options: {', '.join(self.system.EVENT_CONFIGS.keys())}"
            )
            return

        success = self.system.start_event(event_type, hours)

        if success:
            config = self.system.EVENT_CONFIGS[event_type]
            await interaction.response.defer(ephemeral=True)
            await interaction.edit_original_response(
                content=f"{E.CHECK} Started Event: **{config['name']}** for {hours} hours."
            )
            await self._announce(
                f"🚨 **WORLD EVENT STARTED!** 🚨\n\n"
                f"**{config['name']}**\n"
                f"{config['description']}\n\n"
                f"Check `/event_status` for details!"
            )
        else:
            await interaction.response.defer(ephemeral=True)
            await interaction.edit_original_response(content=f"{E.ERROR} Failed to start event.")

    @app_commands.command(
        name="admin_event_end",
        description="[Admin] Manually end the current world event.",
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def admin_end(self, interaction: discord.Interaction):
        """Manually ends the event."""
        self.system.end_current_event()
        await interaction.response.defer(ephemeral=True)
        await interaction.edit_original_response(content=f"{E.CHECK} Event ended manually.")
        await self._announce("✅ **The world returns to normal.** The event has ended.")


async def setup(bot: commands.Bot):
    await bot.add_cog(EventCog(bot))
