"""
cogs/tournament_cog.py

Discord Cog for the Tournament System.
Handles weekly guild tournaments, scheduling, and commands.
"""

import datetime
import logging

import discord
from discord import app_commands
from discord.ext import commands, tasks

import game_systems.data.emojis as E
from database.database_manager import DatabaseManager
from game_systems.guild_system.tournament_system import TournamentSystem

logger = logging.getLogger("eldoria.cogs.tournament")


class TournamentCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = DatabaseManager()
        self.system = TournamentSystem(self.db)

        # Start the background task
        self.check_tournament_cycle.start()
        logger.info("TournamentCog initialized.")

    def cog_unload(self):
        self.check_tournament_cycle.cancel()

    @tasks.loop(hours=1)
    async def check_tournament_cycle(self):
        """
        Runs every hour to check tournament status.
        - Ends expired tournaments.
        - Starts new tournament on Monday.
        """
        try:
            active = self.db.get_active_tournament()
            now = datetime.datetime.now()

            if active:
                end_time = datetime.datetime.fromisoformat(active["end_time"])
                if now > end_time:
                    # End it
                    result_msg = self.system.end_current_tournament()
                    logger.info(f"Tournament Ended Automatically: {result_msg}")
                    await self._announce(f"🏆 **Tournament Concluded!**\n\n{result_msg}")
            else:
                # Start new one if it's Monday
                if now.weekday() == 0:  # Monday
                    t_id = self.system.start_weekly_tournament()
                    logger.info(f"Tournament Started Automatically: ID {t_id}")

                    # Announce start
                    active = self.db.get_active_tournament()
                    if active:
                        await self._announce(
                            f"⚔️ **New Tournament Started!**\n\n"
                            f"Objective: **{active['type'].replace('_', ' ').title()}**\n"
                            f"Ends in: **7 days**"
                        )

        except Exception as e:
            logger.error(f"Error in tournament cycle: {e}", exc_info=True)

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

    @check_tournament_cycle.before_loop
    async def before_check_tournament_cycle(self):
        await self.bot.wait_until_ready()

    # ==================================================================
    # USER COMMANDS
    # ==================================================================

    @app_commands.command(name="tournament_status", description="View the current active Guild Tournament.")
    async def tournament_status(self, interaction: discord.Interaction):
        """Displays the current tournament status."""
        active = self.db.get_active_tournament()

        if not active:
            embed = discord.Embed(
                title=f"{E.VICTORY} No Active Tournament",
                description="The guild hall is quiet. The next tournament will begin on Monday.",
                color=discord.Color.dark_grey(),
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        end_time = datetime.datetime.fromisoformat(active["end_time"])
        time_remaining = end_time - datetime.datetime.now()
        days = time_remaining.days
        hours = time_remaining.seconds // 3600

        embed = discord.Embed(
            title=f"{E.VICTORY} Active Tournament: {active['type'].replace('_', ' ').title()}",
            description="Compete against your guildmates for glory and Aurum!",
            color=discord.Color.gold(),
        )
        embed.add_field(name="Ends In", value=f"{days}d {hours}h", inline=True)

        # Player's Score
        score = self.db.get_player_tournament_score(interaction.user.id, active["id"])
        embed.add_field(name="Your Score", value=f"{score} pts", inline=True)

        embed.set_footer(text="Use /tournament_leaderboard to see top players.")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(
        name="tournament_leaderboard", description="View the top participants in the current tournament."
    )
    async def tournament_leaderboard(self, interaction: discord.Interaction):
        """Displays the leaderboard for the active tournament."""
        active, leaders = self.system.get_leaderboard()

        if not active:
            await interaction.response.send_message(f"{E.WARNING} No tournament is currently active.", ephemeral=True)
            return

        embed = discord.Embed(
            title=f"{E.VICTORY} Leaderboard: {active['type'].replace('_', ' ').title()}", color=discord.Color.gold()
        )

        if not leaders:
            embed.description = "No participants yet. Be the first!"
        else:
            lines = []
            for entry in leaders:
                rank_emoji = (
                    "🥇"
                    if entry["rank"] == 1
                    else "🥈"
                    if entry["rank"] == 2
                    else "🥉"
                    if entry["rank"] == 3
                    else f"#{entry['rank']}"
                )
                name = entry.get("name", "Unknown")
                score = entry["score"]
                lines.append(f"{rank_emoji} **{name}**: {score} pts")
            embed.description = "\n".join(lines)

        await interaction.response.send_message(embed=embed)

    # ==================================================================
    # ADMIN COMMANDS
    # ==================================================================

    @app_commands.command(name="tournament_admin_start", description="[Admin] Manually start a tournament.")
    @app_commands.describe(event_type="Type of event (monster_kills, quests_completed, boss_kills)")
    @app_commands.checks.has_permissions(administrator=True)
    async def admin_start(self, interaction: discord.Interaction, event_type: str = "monster_kills"):
        """Manually starts a tournament."""
        if event_type not in self.system.TOURNAMENT_TYPES:
            await interaction.response.send_message(
                f"{E.ERROR} Invalid type. Options: {', '.join(self.system.TOURNAMENT_TYPES)}", ephemeral=True
            )
            return

        # Force stop any existing
        self.system.end_current_tournament()

        # Start new
        # We modify start logic slightly to support manual type, but since start_weekly picks random,
        # we'll just implement a manual start helper here or override it.
        # Let's call create_tournament directly for manual control.

        start_time = datetime.datetime.now()
        end_time = start_time + datetime.timedelta(days=7)

        t_id = self.db.create_tournament(event_type, start_time.isoformat(), end_time.isoformat())

        await interaction.response.send_message(f"{E.CHECK} Started Tournament #{t_id}: {event_type}", ephemeral=True)

    @app_commands.command(name="tournament_admin_end", description="[Admin] Manually end the current tournament.")
    @app_commands.checks.has_permissions(administrator=True)
    async def admin_end(self, interaction: discord.Interaction):
        """Manually ends the tournament."""
        result = self.system.end_current_tournament()
        await interaction.response.send_message(f"{E.CHECK} Tournament ended manually.\n\n{result}", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(TournamentCog(bot))
