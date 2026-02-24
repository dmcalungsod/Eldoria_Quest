"""
cogs.utils.ui_helpers.py

Shared UI components and navigation callbacks.
Hardened: Async data fetching.
Atmosphere: Profile description restored.
Fix: Added Level and EXP display back to profile.
"""

import asyncio
import logging

import discord

import game_systems.data.emojis as E
from database.database_manager import MAX_INVENTORY_SLOTS, DatabaseManager
from game_systems.crafting.crafting_system import calculate_crafting_xp_req
from game_systems.data.emojis import get_rarity_ansi
from game_systems.items.equipment_manager import EquipmentManager
from game_systems.player.player_stats import PlayerStats

logger = logging.getLogger("eldoria.ui")


def make_progress_bar(
    current: int,
    max_val: int,
    length: int = 10,
    empty_char: str = "░",
    filled_char: str = "█",
) -> str:
    """Generates a visual progress bar string."""
    percent = max(0, min(1, current / max(max_val, 1)))
    filled = int(percent * length)
    return filled_char * filled + empty_char * (length - filled)


def get_health_status_emoji(current: int, max_val: int) -> str:
    """Returns a status emoji based on health percentage."""
    if max_val <= 0:
        return "🔴"

    percent = current / max_val

    if percent > 0.5:
        return "🟢"
    elif percent > 0.2:
        return "🟡"
    return "🔴"


def build_inventory_embed(items: list, max_slots: int = MAX_INVENTORY_SLOTS) -> discord.Embed:
    """Constructs the inventory display."""
    # Only count unequipped items (backpack slots)
    slot_count = len([i for i in items if not i.get("equipped")])
    embed = discord.Embed(
        title=f"{E.BACKPACK} Backpack ({slot_count}/{max_slots})",
        color=discord.Color.dark_orange(),
    )

    # Capacity Bar
    progress = make_progress_bar(slot_count, max_slots, length=12)
    embed.description = f"**Capacity:** `{progress}` {slot_count}/{max_slots}"

    if not items:
        embed.description += "\n\n*Your pack is light, holding only dust and echoes.*"
        return embed

    equipped_groups = {
        "Weapon": [],
        "Armor": [],
        "Accessory": [],
    }

    categories = {"Equipment": [], "Consumable": [], "Material": [], "Misc": []}
    unequipped_counts = {}

    for item in items:
        itype = item["item_type"].title()
        rarity = item.get("rarity", "Common")
        name = item["item_name"]

        if item.get("equipped"):
            slot_key = item.get("slot", "")
            slot_display = slot_key.replace("_", " ").title()

            # Categorize Slot
            cat = "Armor"  # Default
            if slot_key in EquipmentManager.TWO_HANDED_SLOTS or slot_key in EquipmentManager.MAIN_HAND_SLOTS:
                cat = "Weapon"
            elif slot_key in EquipmentManager.OFF_HAND_SLOTS:
                # Shields are armor, others are weapons
                if slot_key == "shield":
                    cat = "Armor"
                else:
                    cat = "Weapon"
            elif slot_key == "accessory":
                cat = "Accessory"

            equipped_groups[cat].append(get_rarity_ansi(rarity, f"• {name} ({slot_display})"))
        else:
            key = (itype, name, rarity)
            unequipped_counts[key] = unequipped_counts.get(key, 0) + item["count"]

    # --- EQUIPPED SECTION ---
    has_equipped = any(equipped_groups.values())
    if has_equipped:
        val = ""
        if equipped_groups["Weapon"]:
            val += "**Weapons**\n" + "\n".join(equipped_groups["Weapon"]) + "\n"
        if equipped_groups["Armor"]:
            val += "**Armor**\n" + "\n".join(equipped_groups["Armor"]) + "\n"
        if equipped_groups["Accessory"]:
            # Display capacity for accessories
            acc_count = len(equipped_groups["Accessory"])
            limit = EquipmentManager.MAX_ACCESSORY_SLOTS
            val += f"**Accessories ({acc_count}/{limit})**\n" + "\n".join(equipped_groups["Accessory"]) + "\n"

        embed.add_field(name="⚔️ Equipped Gear", value=f"```ansi\n{val}```", inline=False)

    # --- INVENTORY SECTION ---
    for (itype, name, rarity), count in sorted(unequipped_counts.items()):
        cat = itype if itype in categories else "Misc"
        text = f"• {name} (x{count})"
        categories[cat].append(get_rarity_ansi(rarity, text))

    for cat, lines in categories.items():
        if lines:
            val = "```ansi\n" + "\n".join(lines[:15]) + "\n```"
            if len(lines) > 15:
                val += f"\n*(...and {len(lines) - 15} more)*"
            embed.add_field(name=cat, value=val, inline=False)

    return embed


async def get_player_or_error(
    interaction: discord.Interaction,
    db: DatabaseManager,
    content: str = "Character record not found.",
) -> dict | None:
    """
    Fetches the player record. If not found, sends an ephemeral error message.
    Returns the player dict or None.
    """
    player = await asyncio.to_thread(db.get_player, interaction.user.id)
    if not player:
        if not interaction.response.is_done():
            await interaction.response.send_message(content, ephemeral=True)
        else:
            await interaction.followup.send(content, ephemeral=True)
        return None
    return player


async def get_profile_bundle_or_error(
    interaction: discord.Interaction,
    db: DatabaseManager,
    content: str = "Character record not found.",
) -> dict | None:
    """
    Fetches the profile bundle. If not found, sends an ephemeral error message.
    Returns the bundle dict or None.
    """
    # Apply passive regeneration before fetching profile
    await asyncio.to_thread(db.apply_passive_regen, interaction.user.id)

    bundle = await asyncio.to_thread(db.get_profile_bundle, interaction.user.id)
    if not bundle:
        if not interaction.response.is_done():
            await interaction.response.send_message(content, ephemeral=True)
        else:
            await interaction.followup.send(content, ephemeral=True)
        return None
    return bundle


async def back_to_profile_callback(interaction: discord.Interaction, is_new_message: bool = False):
    """Navigation: Returns to Character Profile."""
    from game_systems.character.ui.profile_view import CharacterTabView

    if not interaction.response.is_done():
        await interaction.response.defer()

    db = DatabaseManager()
    discord_id = interaction.user.id

    try:
        # Optimized: Fetch Player, Stats, and Guild in one go
        bundle = await get_profile_bundle_or_error(interaction, db)
        if not bundle:
            return

        player = bundle["player"]
        stats_data = bundle["stats"]
        guild_data = bundle["guild"]

        # Fetch Class (Cached)
        class_data = await asyncio.to_thread(db.get_class, player["class_id"])

        stats = PlayerStats.from_dict(stats_data)
        class_name = class_data["name"] if class_data else "Unknown"
        active_title = player.get("active_title")

        title_display = f" *{active_title}*" if active_title else ""

        description = (
            f"**Name:** {player['name']}{title_display}\n"
            f"**Occupation:** Adventurer\n"
            f"**Class:** {class_name}\n\n"
            "*Registered with the Grand Archive of Astraeon. "
            "A soul bound to the exploration of the unknown.*"
        )

        embed = discord.Embed(
            title=f"{E.SCROLL} Character Status",
            description=description,
            color=discord.Color.dark_red(),
        )

        if interaction.user.avatar:
            embed.set_thumbnail(url=interaction.user.avatar.url)

        # Fetch Inventory Count (Async)
        inv_count = await asyncio.to_thread(db.get_inventory_slot_count, discord_id)
        max_slots = stats.max_inventory_slots

        # Vitals & Level (FIXED)
        hp_bar = make_progress_bar(player["current_hp"], stats.max_hp)
        mp_bar = make_progress_bar(player["current_mp"], stats.max_mp)
        exp_bar = make_progress_bar(player["experience"], player["exp_to_next"])
        status_emoji = get_health_status_emoji(player["current_hp"], stats.max_hp)

        embed.add_field(
            name=f"Condition {status_emoji}",
            value=(
                f"**Level:** {player['level']}\n"
                f"**EXP:** `{exp_bar}` {player['experience']} / {player['exp_to_next']}\n"
                f"{E.HP} **HP:** `{hp_bar}` {player['current_hp']} / {stats.max_hp}\n"
                f"{E.MP} **MP:** `{mp_bar}` {player['current_mp']} / {stats.max_mp}\n"
                f"{E.BACKPACK} **Bag:** {inv_count} / {max_slots}"
            ),
            inline=True,
        )

        # Rank
        rank = guild_data["rank"] if guild_data else "Unregistered"
        embed.add_field(name="Guild Rank", value=f"**{rank}**", inline=True)

        # Crafting
        craft_level = player.get("crafting_level", 1)
        craft_xp = player.get("crafting_xp", 0)
        craft_req = calculate_crafting_xp_req(craft_level)
        craft_bar = make_progress_bar(craft_xp, craft_req, length=8)

        embed.add_field(
            name="🛠️ Crafting",
            value=f"**Level {craft_level}**\n`{craft_bar}` {craft_xp}/{craft_req}",
            inline=True,
        )

        # Stats
        stat_block = (
            f"{E.STR} `STR: {stats.strength:<3}` {E.END} `END: {stats.endurance:<3}` {E.DEX} `DEX: {stats.dexterity:<3}`\n"
            f"{E.AGI} `AGI: {stats.agility:<3}` {E.MAG} `MAG: {stats.magic:<3}` {E.LCK} `LCK: {stats.luck:<3}`"
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
        # Validate player existence first
        player = await get_player_or_error(interaction, db)
        if not player:
            return

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
            color=discord.Color.dark_gold(),
        )

        embed.add_field(
            name="📜 Quest Board",
            value="Review available contracts and report successes.",
            inline=False,
        )
        embed.add_field(
            name="⚙️ Guild Services",
            value="Access the Shop, Exchange, Infirmary, or Training Grounds.",
            inline=False,
        )

        view = GuildLobbyView(db, interaction.user, rank=card["rank"])
        await interaction.edit_original_response(embed=embed, view=view)

    except Exception as e:
        logger.error(f"Guild Hall load error: {e}")
