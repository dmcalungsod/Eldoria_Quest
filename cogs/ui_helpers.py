"""
ui_helpers.py

Shared UI components and navigation callbacks.
Hardened against missing data and API errors.
"""

import asyncio
import logging
import discord
import game_systems.data.emojis as E
from database.database_manager import DatabaseManager
from game_systems.data.emojis import get_rarity_ansi
from game_systems.player.player_stats import PlayerStats

logger = logging.getLogger("eldoria.ui")

def build_inventory_embed(items: list) -> discord.Embed:
    """Constructs the inventory display."""
    embed = discord.Embed(title=f"{E.BACKPACK} Backpack", color=discord.Color.dark_orange())

    if not items:
        embed.description = "Your backpack is empty."
        return embed

    equipped = []
    categories = {"Equipment": [], "Consumable": [], "Material": [], "Misc": []}
    
    # Aggregate unequipped items for display
    unequipped_counts = {} # (type, name, rarity) -> count

    for item in items:
        itype = item["item_type"].title()
        rarity = item.get("rarity", "Common")
        name = item["item_name"]
        
        if item.get("equipped"):
            slot = item.get("slot", "Unknown").replace("_", " ").title()
            equipped.append(get_rarity_ansi(rarity, f"[E] {name} ({slot})"))
        else:
            key = (itype, name, rarity)
            unequipped_counts[key] = unequipped_counts.get(key, 0) + item["count"]

    # Format Lists
    for (itype, name, rarity), count in sorted(unequipped_counts.items()):
        cat = itype if itype in categories else "Misc"
        text = f"• {name} (x{count})"
        categories[cat].append(get_rarity_ansi(rarity, text))

    if equipped:
        embed.add_field(name="Equipped Gear", value="```ansi\n" + "\n".join(equipped) + "\n```", inline=False)

    for cat, lines in categories.items():
        if lines:
            # Chunking to prevent embed limits (1024 chars)
            # Simplified here, but in prod consider chunking logic
            val = "```ansi\n" + "\n".join(lines[:15]) + "\n```" 
            if len(lines) > 15: val += f"\n*(...and {len(lines)-15} more)*"
            embed.add_field(name=cat, value=val, inline=False)

    return embed

async def back_to_profile_callback(interaction: discord.Interaction, is_new_message: bool = False):
    """Navigation: Returns to Character Profile."""
    # Avoid circular imports
    from game_systems.character.ui.profile_view import CharacterTabView

    if not interaction.response.is_done():
        await interaction.response.defer()

    db = DatabaseManager()
    discord_id = interaction.user.id

    try:
        # Parallel Data Fetch
        tasks = [
            asyncio.to_thread(db.get_player, discord_id),
            asyncio.to_thread(db.get_guild_member_data, discord_id),
            asyncio.to_thread(db.get_player_stats_json, discord_id),
            asyncio.to_thread(db.get_player_skills, discord_id)
        ]
        results = await asyncio.gather(*tasks)
        
        player, guild_data, stats_json, skills = results

        if not player:
            await interaction.followup.send("Character not found.", ephemeral=True)
            return

        stats = PlayerStats.from_dict(stats_json)
        
        # Build Embed
        embed = discord.Embed(
            title=f"{E.SCROLL} {player['name']}'s Status",
            description=f"**Class:** Adventurer", # In real app fetch class name
            color=discord.Color.dark_red()
        )
        
        if interaction.user.avatar:
            embed.set_thumbnail(url=interaction.user.avatar.url)

        embed.add_field(
            name="Vitals",
            value=f"{E.HP} **HP:** {player['current_hp']}/{stats.max_hp}\n{E.MP} **MP:** {player['current_mp']}/{stats.max_mp}",
            inline=True
        )
        
        rank = guild_data['rank'] if guild_data else "Unregistered"
        embed.add_field(name="Guild Rank", value=f"**{rank}**", inline=True)
        
        stat_block = (
            f"`STR: {stats.strength:<3}` `END: {stats.endurance:<3}` `DEX: {stats.dexterity:<3}`\n"
            f"`AGI: {stats.agility:<3}` `MAG: {stats.magic:<3}` `LCK: {stats.luck:<3}`"
        )
        embed.add_field(name="Attributes", value=stat_block, inline=False)

        view = CharacterTabView(db, interaction.user)
        
        if is_new_message:
            await interaction.followup.send(embed=embed, view=view)
        else:
            await interaction.edit_original_response(embed=embed, view=view)
            
    except Exception as e:
        logger.error(f"Profile load error for {discord_id}: {e}", exc_info=True)
        if not interaction.response.is_done():
            await interaction.response.send_message("Error loading profile.", ephemeral=True)

async def back_to_guild_hall_callback(interaction: discord.Interaction):
    from game_systems.guild_system.ui.lobby_view import GuildLobbyView

    if not interaction.response.is_done():
        await interaction.response.defer()

    db = DatabaseManager()
    try:
        card = await asyncio.to_thread(db.get_guild_card_data, interaction.user.id)
        if not card:
            await interaction.followup.send("You are not a guild member.", ephemeral=True)
            return

        embed = discord.Embed(
            title="🏰 Adventurer’s Guild Hall",
            description=f"Welcome, **{card['name']}** (Rank {card['rank']}).",
            color=discord.Color.dark_gold()
        )
        # Add menu fields...
        embed.add_field(name="Services", value="Quests, Shop, Exchange, Training", inline=False)

        view = GuildLobbyView(db, interaction.user)
        await interaction.edit_original_response(embed=embed, view=view)

    except Exception as e:
        logger.error(f"Guild Hall load error: {e}")