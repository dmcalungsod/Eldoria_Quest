import logging

import discord

logger = logging.getLogger("eldoria.cogs.announcer")

async def announce_to_guilds(bot, message: str):
    """Attempts to announce a message to a guild channel (guild-hall or general)."""
    for guild in bot.guilds:
        channel = discord.utils.get(guild.text_channels, name="guild-hall")
        if not channel:
            channel = discord.utils.get(guild.text_channels, name="general")

        if channel:
            try:
                await channel.send(message)
            except Exception as e:
                logger.error(f"Failed to announce in {guild.name}: {e}")
