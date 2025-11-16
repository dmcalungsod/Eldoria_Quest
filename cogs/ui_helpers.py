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
import asyncio  # <-- 1. IMPORT ASYNCIO

# --- NEW IMPORT ---
from game_systems.items.item_manager import item_manager

# --- END NEW ---

from game_systems.data.emojis import get_rarity_ansi


# ======================================================================
# EMBED BUILDER
# ======================================================================


# ... (build_inventory_embed function is unchanged) ...
def build_inventory_embed(items: list) -> discord.Embed:
    """
    Builds the standard embed for the player's inventory,
    separating items by type and equipped status.

    --- NOW WITH ANSI COLORS & SIMPLIFIED FORMAT ---
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

            # --- THIS IS THE FIX (User request to simplify format) ---
            # We no longer fetch or display individual stats in the list.
            
            # 1. Get the slot, capitalize it if it exists
            slot_name = item.get('slot', 'Unknown')
            if slot_name:
                # Turns 'heavy_armor' into 'Heavy Armor'
                slot_name = slot_name.replace('_', ' ').title()

            if item["equipped"] == 1:
                # New format: [E] Item Name (Slot)
                text = f"[E] {item['item_name']} ({slot_name})"
                categories["Equipped"].append(get_rarity_ansi(rarity, text))
            else:
                # New format: • Item Name (xCount)
                # (Slot/stats are hidden for unequipped items to reduce clutter)
                text = f"• {item['item_name']} (x{item['count']})"
                categories["Equipment"].append(get_rarity_ansi(rarity, text))
            # --- END OF FIX ---

        elif item_type in categories:
            # Format for Materials/Consumables
            text = f"• {item['item_name']} (x{item['count']})"
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


# --- 2. THIS ENTIRE FUNCTION IS REWRITTEN ---
async def back_to_profile_callback(
    interaction: discord.Interaction, is_new_message: bool = False
):
    """
    A shared callback to return to the MAIN Character Profile menu.
    This is the new "home" screen.
    This function is now ASYNCHRONOUS to prevent blocking the bot.
    """
    # FIX: Import the new CharacterTabView
    from .character_cog import CharacterTabView

    if not interaction.response.is_done():
        await interaction.response.defer()

    discord_id = interaction.user.id
    db = DatabaseManager()

    # --- Build the Profile Embed ---

    # Run all blocking database calls in separate threads
    player = await asyncio.to_thread(db.get_player, discord_id)
    if not player:
        await interaction.followup.send(
            "Error: Could not find player data.", ephemeral=True
        )
        return

    # Run these calls in parallel
    guild_data_task = asyncio.to_thread(db.get_guild_member_data, discord_id)
    stats_json_task = asyncio.to_thread(db.get_player_stats_json, discord_id)
    class_row_task = asyncio.to_thread(db.get_class, player["class_id"])
    player_skills_task = asyncio.to_thread(db.get_player_skills, discord_id)

    # Wait for all of them to finish
    guild_data, stats_json, class_row, player_skills = await asyncio.gather(
        guild_data_task, stats_json_task, class_row_task, player_skills_task
    )

    # Now that all data is loaded, we can build the embed
    stats = PlayerStats.from_dict(stats_json)
    class_name = class_row["name"] if class_row else "Unknown"

    embed = discord.Embed(
        title=f"{E.SCROLL} {player['name']}'s Character Status",
        description=f"**Occupation:** Adventurer\n**Class:** {class_name}",
        color=discord.Color.dark_red(),
    )

    if interaction.user.avatar:
        embed.set_thumbnail(url=interaction.user.avatar.url)

    embed.add_field(
        name="Condition",
        value=f"**Lv.** {player['level']}\n**Rank:** {guild_data['rank'] if guild_data else 'N/A'}",
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
    embed.add_field(name="Overall Abilities", value=stat_block, inline=False)

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

    # FIX: Attach the new CharacterTabView
    view = CharacterTabView(db, interaction.user)

    if is_new_message:
        await interaction.followup.send(embed=embed, view=view, ephemeral=False)
    else:
        await interaction.edit_original_response(content=None, embed=embed, view=view)


async def back_to_guild_hall_callback(interaction: discord.Interaction):
    """
    A shared callback to return to the Guild Hall SUB-MENU.
    This always edits the message.
    """
    # FIX: Import GuildLobbyView instead of GuildCardView
    from .guild_hub_cog import GuildLobbyView

    if not interaction.response.is_done():
        await interaction.response.defer()

    discord_id = interaction.user.id
    db = DatabaseManager()

    card_data = await asyncio.to_thread(db.get_guild_card_data, discord_id)

    if not card_data:
        await interaction.edit_original_response(
            content="Error: Could not find guild data.", embed=None, view=None
        )
        return

    # --- THIS IS YOUR NEW THEMATIC EMBED ---
    embed = discord.Embed(
        title="🏰 Adventurer’s Guild Lobby",
        description=(
            "*The receptionist inspects your guild card and bows politely.*\n\n"
            f"**{card_data['name']} — Rank {card_data['rank']}**\n"
            "“How may the Guild assist you today?”"
        ),
        color=discord.Color.dark_gold(),
    )

    embed.add_field(
        name="📜 Quest Board",
        value=(
            "• **Available Quests** — View open missions\n"
            "• **Current Progress** — Track ongoing assignments\n"
            "• **Rank Trials** — Attempt promotion exams"
        ),
        inline=False
    )

    embed.add_field(
        name="⚙️ Guild Services",
        value=(
            "• **Guild Shop** — Buy supplies and equipment\n"
            "• **Item Exchange** — Trade materials and rare items\n"
            "• **Facilities** — Training grounds & workshops"
        ),
        inline=False
    )
    
    embed.set_footer(text="Select an option below.")
    # --- END OF EMBED ---

    # FIX: Attach the new GuildLobbyView
    view = GuildLobbyView(db, interaction.user)
    await interaction.edit_original_response(content=None, embed=embed, view=view)