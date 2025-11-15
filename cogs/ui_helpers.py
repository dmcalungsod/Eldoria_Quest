"""
ui_helpers.py

Contains shared helper functions for the UI, primarily the
global "back" button callback to prevent circular imports.
"""

import discord
from database.database_manager import DatabaseManager
import game_systems.data.emojis as E


async def back_to_guild_card_callback(
    interaction: discord.Interaction, embed_to_show: discord.Embed = None
):
    """
    A shared callback to return to the main Guild Card menu.
    This prevents code duplication.
    """
    # We import here, inside the function, to prevent circular imports
    # at the top level.
    from .guild_hub_cog import GuildCardView

    # Defer the response if it's the first action
    if not interaction.response.is_done():
        await interaction.response.defer()

    # If we have a receipt (like from selling), show it ephemerally
    if embed_to_show:
        await interaction.followup.send(embed=embed_to_show, ephemeral=True)

    discord_id = interaction.user.id
    db = DatabaseManager()
    conn = db.connect()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT p.name, c.name as class_name, p.level, p.experience, gm.rank, gm.join_date
        FROM players p
        JOIN classes c ON p.class_id = c.id
        JOIN guild_members gm ON p.discord_id = gm.discord_id
        WHERE p.discord_id = ?
    """,
        (discord_id,),
    )
    card_data = cur.fetchone()
    conn.close()

    if not card_data:
        await interaction.edit_original_response(
            content=f"{E.ERROR} Error retrieving your Guild Card.",
            embed=None,
            view=None,
        )
        return

    embed = discord.Embed(
        title=f"{E.SCROLL} Guild Card",
        description=f"This card certifies that **{card_data['name']}** is a registered member of The Eldorian Adventurer’s Consortium.",
        color=discord.Color.dark_gold(),
    )
    embed.add_field(name="Class", value=card_data["class_name"], inline=True)
    embed.add_field(name="Rank", value=card_data["rank"], inline=True)
    embed.add_field(name="Level", value=card_data["level"], inline=True)
    embed.add_field(
        name="Experience", value=f"{card_data['experience']} XP", inline=True
    )
    embed.set_footer(text=f"Joined: {card_data['join_date']}")

    view = GuildCardView(db)
    await interaction.edit_original_response(embed=embed, view=view)
