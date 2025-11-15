"""
_ui_helpers.py

Contains shared helper functions for the UI, primarily the
global "back" button callbacks for the main UI hubs.
This is the core of the "single-UI" navigation.
"""

import discord
from database.database_manager import DatabaseManager
from game_systems.player.player_stats import PlayerStats
import game_systems.data.emojis as E


async def back_to_profile_callback(
    interaction: discord.Interaction, embed_to_show: discord.Embed = None
):
    """
    A shared callback to return to the MAIN Character Profile menu.
    This is the new "home" screen.
    """
    # We import here, inside the function, to prevent circular imports
    from .guild_hub_cog import CharacterProfileView

    if not interaction.response.is_done():
        await interaction.response.defer()

    if embed_to_show:
        await interaction.followup.send(embed=embed_to_show, ephemeral=True)

    discord_id = interaction.user.id
    db = DatabaseManager()

    # --- Build the Profile Embed ---
    player = db.get_player(discord_id)
    if not player:
        await interaction.edit_original_response(
            content="Error: Could not find player.", embed=None, view=None
        )
        return

    conn = db.connect()
    cur = conn.cursor()
    cur.execute("SELECT rank FROM guild_members WHERE discord_id = ?", (discord_id,))
    guild_data = cur.fetchone()
    conn.close()

    stats_json = db.get_player_stats_json(discord_id)
    stats = PlayerStats.from_dict(stats_json)
    class_row = db.get_class(player["class_id"])
    class_name = class_row["name"] if class_row else "Unknown"

    embed = discord.Embed(
        title=f"{E.SCROLL} Adventurer Status — {player['name']}",
        description=f"**Guild:** Adventurer's Guild\n**Class:** {class_name}",
        color=discord.Color.dark_red(),
    )
    embed.add_field(
        name="Condition",
        value=f"**Lv.** {player['level']}\n**Rank:** {guild_data['rank']}",
        inline=True,
    )
    embed.add_field(
        name="Vitals",
        value=f"{E.HP} **HP:** {stats.max_hp}\n{E.MP} **MP:** {stats.max_mp}",
        inline=True,
    )
    stat_block = (
        f"`STR: {stats.strength:<3}` `END: {stats.endurance:<3}` `DEX: {stats.dexterity:<3}`\n"
        f"`AGI: {stats.agility:<3}` `MAG: {stats.magic:<3}` `LCK: {stats.luck:<3}`"
    )
    embed.add_field(name="Basic Abilities", value=stat_block, inline=False)

    # --- Create the View ---
    view = CharacterProfileView(db)

    await interaction.edit_original_response(content=None, embed=embed, view=view)


async def back_to_guild_hall_callback(
    interaction: discord.Interaction, embed_to_show: discord.Embed = None
):
    """
    A shared callback to return to the Guild Hall SUB-MENU.
    """
    # We import here, inside the function, to prevent circular imports
    from .guild_hub_cog import GuildCardView

    if not interaction.response.is_done():
        await interaction.response.defer()

    if embed_to_show:
        await interaction.followup.send(embed=embed_to_show, ephemeral=True)

    discord_id = interaction.user.id
    db = DatabaseManager()

    # --- Build the Guild Card Embed ---
    conn = db.connect()
    cur = conn.cursor()
    cur.execute(
        "SELECT p.name, gm.rank, gm.join_date FROM players p "
        "JOIN guild_members gm ON p.discord_id = gm.discord_id "
        "WHERE p.discord_id = ?",
        (discord_id,),
    )
    card_data = cur.fetchone()
    conn.close()

    if not card_data:
        await interaction.edit_original_response(
            content="Error: Could not find guild data.", embed=None, view=None
        )
        return

    embed = discord.Embed(
        title=f"{E.SCROLL} Guild Card",
        description=f"This card certifies that **{card_data['name']}** is a registered member of the **Adventurer's Guild** (Ashgrave City branch).",
        color=discord.Color.dark_gold(),
    )
    embed.add_field(name="Rank", value=card_data["rank"], inline=True)
    embed.set_footer(text=f"Joined: {card_data['join_date']}")

    # --- Create the View ---
    view = GuildCardView(db)
    await interaction.edit_original_response(content=None, embed=embed, view=view)
