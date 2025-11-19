"""
cogs/ui_helpers.py

Shared UI components and navigation callbacks.
Hardened: Async data fetching.
Atmosphere: Profile description restored.
Fix: Added Level and EXP display back to profile.
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
        embed.description = "*Your pack is light, holding only dust and echoes.*"
        return embed

    equipped = []
    categories = {"Equipment": [], "Consumable": [], "Material": [], "Misc": []}
    
    unequipped_counts = {} 

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

    for (itype, name, rarity), count in sorted(unequipped_counts.items()):
        cat = itype if itype in categories else "Misc"
        text = f"• {name} (x{count})"
        categories[cat].append(get_rarity_ansi(rarity, text))

    if equipped:
        embed.add_field(name="Equipped Gear", value="```ansi\n" + "\n".join(equipped) + "\n```", inline=False)

    for cat, lines in categories.items():
        if lines:
            val = "```ansi\n" + "\n".join(lines[:15]) + "\n```" 
            if len(lines) > 15: val += f"\n*(...and {len(lines)-15} more)*"
            embed.add_field(name=cat, value=val, inline=False)

    return embed

async def back_to_profile_callback(interaction: discord.Interaction, is_new_message: bool = False):
    """Navigation: Returns to Character Profile."""
    from game_systems.character.ui.profile_view import CharacterTabView

    if not interaction.response.is_done():
        await interaction.response.defer()

    db = DatabaseManager()
    discord_id = interaction.user.id

    try:
        player = await asyncio.to_thread(db.get_player, discord_id)

        if not player:
            await interaction.followup.send("Character record not found.", ephemeral=True)
            return

        tasks = [
            asyncio.to_thread(db.get_guild_member_data, discord_id),
            asyncio.to_thread(db.get_player_stats_json, discord_id),
            asyncio.to_thread(db.get_player_skills, discord_id),
            asyncio.to_thread(db.get_class, player["class_id"])
        ]
        results = await asyncio.gather(*tasks)
        
        guild_data, stats_json, skills, class_data = results
        stats = PlayerStats.from_dict(stats_json)
        class_name = class_data["name"] if class_data else "Unknown"
        
        description = (
            f"**Name:** {player['name']}\n"
            f"**Occupation:** Adventurer\n"
            f"**Class:** {class_name}\n\n"
            "*Registered with the Grand Archive of Astraeon. "
            "A soul bound to the exploration of the unknown.*"
        )

        embed = discord.Embed(
            title=f"{E.SCROLL} Character Status",
            description=description,
            color=discord.Color.dark_red()
        )
        
        if interaction.user.avatar:
            embed.set_thumbnail(url=interaction.user.avatar.url)

        # Vitals & Level (FIXED)
        embed.add_field(
            name="Condition",
            value=(
                f"**Level:** {player['level']}\n"
                f"**EXP:** {player['experience']} / {player['exp_to_next']}\n"
                f"{E.HP} **HP:** {player['current_hp']} / {stats.max_hp}\n"
                f"{E.MP} **MP:** {player['current_mp']} / {stats.max_mp}"
            ),
            inline=True
        )
        
        # Rank
        rank = guild_data['rank'] if guild_data else "Unregistered"
        embed.add_field(name="Guild Rank", value=f"**{rank}**", inline=True)
        
        # Stats
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
            description=(
                f"*The receptionist nods as you approach.*\n\n"
                f"**{card['name']} — Rank {card['rank']}**\n"
                "*“How may the Guild assist you today, Adventurer?”*"
            ),
            color=discord.Color.dark_gold()
        )
        
        embed.add_field(
            name="📜 Quest Board",
            value="Review available contracts and report successes.",
            inline=False
        )
        embed.add_field(
            name="⚙️ Guild Services",
            value="Access the Shop, Exchange, Infirmary, or Training Grounds.",
            inline=False
        )

        view = GuildLobbyView(db, interaction.user)
        await interaction.edit_original_response(embed=embed, view=view)

    except Exception as e:
        logger.error(f"Guild Hall load error: {e}")