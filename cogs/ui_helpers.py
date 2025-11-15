"""
ui_helpers.py

Contains shared helper functions for the UI, primarily the
global "back" button callbacks for the main UI hubs.
This is the core of the "single-UI" navigation.
"""

import discord
from database.database_manager import DatabaseManager
from game_systems.player.player_stats import PlayerStats
import game_systems.data.emojis as E

# --- THIS IS THE FIX ---
# Import the helper function from its new central location
from game_systems.data.emojis import get_rarity_ansi

# --- END OF FIX ---


# ======================================================================
# EMBED BUILDER
# ======================================================================


def build_inventory_embed(items: list) -> discord.Embed:
    """
    Builds the standard embed for the player's inventory,
    separating items by type and equipped status.

    --- NOW WITH ANSI COLORS ---
    """
    embed = discord.Embed(
        title=f"{E.BACKPACK} Backpack", color=discord.Color.dark_orange()
    )

    categories = {
        "Equipped": [],
        "Equipment": [],
        "Consumable": [],
        "Material": [],
    }

    for item in items:
        item_type = item["item_type"].title()
        rarity = (
            item.get("rarity") or "Common"
        )  # Default to Common if rarity is None or empty

        text = ""  # This will be the text we color

        if item_type == "Equipment":
            if item["equipped"] == 1:
                # Build string WITHOUT markdown
                text = f"• {item['item_name']} ({rarity}) (Slot: {item['slot']})"
                # Add the color-wrapped string to the list
                categories["Equipped"].append(get_rarity_ansi(rarity, text))
            else:
                text = f"• {item['item_name']} ({rarity}) (x{item['count']})"
                categories["Equipment"].append(get_rarity_ansi(rarity, text))

        elif item_type in categories:
            text = f"• {item['item_name']} ({rarity}) (x{item['count']})"
            categories[item_type].append(get_rarity_ansi(rarity, text))

    if not any(categories.values()):
        embed.description = "Your backpack is empty."
        return embed

    if categories["Equipped"]:
        value = "```ansi\n" + "\n".join(categories["Equipped"]) + "\n```"
        embed.add_field(name="Equipped Gear", value=value, inline=False)

    for category, item_list in categories.items():
        if category != "Equipped" and item_list:
            value = "```ansi\n" + "\n".join(item_list) + "\n```"
            embed.add_field(name=category, value=value, inline=False)

    return embed


# ======================================================================
# VIEW CALLBACKS
# ======================================================================


async def back_to_profile_callback(
    interaction: discord.Interaction, is_new_message: bool = False
):
    """
    A shared callback to return to the MAIN Character Profile menu.
    This is the new "home" screen.
    If is_new_message=True, it sends a new message.
    Otherwise, it edits the existing one.
    """
    from .character_cog import CharacterProfileView

    if not interaction.response.is_done():
        await interaction.response.defer()

    discord_id = interaction.user.id
    db = DatabaseManager()

    # --- Build the Profile Embed ---
    player = db.get_player(discord_id)
    if not player:
        await interaction.followup.send(
            "Error: Could not find player data.", ephemeral=True
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

    player_skills = db.get_player_skills(discord_id)

    embed = discord.Embed(
        title=f"{E.SCROLL} Adventurer Status — {player['name']}",
        description=f"**Guild:** Adventurer's Guild\n**Class:** {class_name}",
        color=discord.Color.dark_red(),
    )

    if interaction.user.avatar:
        embed.set_thumbnail(url=interaction.user.avatar.url)

    embed.add_field(
        name="Condition",
        value=f"**Lv.** {player['level']}\n**Rank:** {guild_data['rank']}",
        inline=True,
    )

    embed.add_field(
        name="Vitals",
        value=(
            f"{E.HP} **HP:** {player['current_hp']} / {stats.max_hp}\n"
            f"{E.MP} **MP:** {player['current_mp']} / {stats.max_mp}"
        ),
        inline=True,
    )

    stat_block = (
        f"`STR: {stats.strength:<3}` `END: {stats.endurance:<3}` `DEX: {stats.dexterity:<3}`\n"
        f"`AGI: {stats.agility:<3}` `MAG: {stats.magic:<3}` `LCK: {stats.luck:<3}`"
    )
    embed.add_field(name="Basic Abilities", value=stat_block, inline=False)

    if not player_skills:
        skills_str = "No skills learned."
    else:
        active_skills = []
        passive_skills = []
        for s in player_skills:
            skill_line = f"• **{s['name']}** (Lv. {s['skill_level']})"
            if s["type"] == "Active":
                active_skills.append(skill_line)
            else:
                passive_skills.append(skill_line)

        skills_parts = []
        if active_skills:
            skills_parts.append(f"**Active**\n" + "\n".join(active_skills))
        if passive_skills:
            skills_parts.append(f"**Passive**\n" + "\n".join(passive_skills))

        skills_str = "\n".join(skills_parts)

    embed.add_field(name="Acquired Skills", value=skills_str, inline=False)

    view = CharacterProfileView(db, interaction.user)

    if is_new_message:
        await interaction.followup.send(embed=embed, view=view, ephemeral=False)
    else:
        await interaction.edit_original_response(content=None, embed=embed, view=view)


async def back_to_guild_hall_callback(interaction: discord.Interaction):
    """
    A shared callback to return to the Guild Hall SUB-MENU.
    This always edits the message.
    """
    from .guild_hub_cog import GuildCardView

    if not interaction.response.is_done():
        await interaction.response.defer()

    discord_id = interaction.user.id
    db = DatabaseManager()

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

    view = GuildCardView(db, interaction.user)
    await interaction.edit_original_response(content=None, embed=embed, view=view)
