"""
ui_helpers.py

Shared helper utilities for the UI system, including global
'navigation' callbacks used by the core single-UI layout.

Ensures consistent transitions between menus such as:
- Character Profile
- Guild Hall
- Inventory & Equipment
- Skill Management
"""

import asyncio

import discord

import game_systems.data.emojis as E
from database.database_manager import DatabaseManager
from game_systems.data.emojis import get_rarity_ansi
from game_systems.player.player_stats import PlayerStats

# ======================================================================
# EMBED BUILDER
# ======================================================================

def build_inventory_embed(items: list) -> discord.Embed:
    """
    Construct the standardized inventory embed.

    Features:
    - Separates equipped gear from backpack contents.
    - Aggregates identical unequipped items (type + name + rarity).
    - Uses ANSI rarity coloring for clean visual distinction.
    - Sorted output for a consistent UX across all inventory views.
    """
    embed = discord.Embed(
        title=f"{E.BACKPACK} Backpack",
        color=discord.Color.dark_orange(),
    )

    equipped_list = []

    # (item_type, item_name, rarity) → total_count
    unequipped_aggregation = {}

    for item in items:
        item_type = item["item_type"].title()
        rarity = item.get("rarity") or "Common"
        name = item["item_name"]
        count = item["count"]

        # Equipped equipment (always displayed individually)
        if item.get("equipped") == 1 and item_type == "Equipment":
            slot_name = item.get("slot", "Unknown").replace("_", " ").title()
            text = f"[E] {name} ({slot_name})"
            equipped_list.append(get_rarity_ansi(rarity, text))
            continue

        # Aggregate unequipped items
        key = (item_type, name, rarity)
        unequipped_aggregation[key] = unequipped_aggregation.get(key, 0) + count

    categories = {
        "Equipped": equipped_list,
        "Equipment": [],
        "Consumable": [],
        "Material": [],
    }

    # Sort by type → name for clean ordering
    sorted_items = sorted(
        unequipped_aggregation.items(),
        key=lambda x: (x[0][0], x[0][1]),
    )

    for (itype, name, rarity), total_count in sorted_items:
        text = f"• {name} (x{total_count})"
        colored_text = get_rarity_ansi(rarity, text)

        if itype in categories:
            categories[itype].append(colored_text)
        else:
            categories.setdefault("Misc", []).append(colored_text)

    # If no items
    if not any(categories.values()):
        embed.description = "Your backpack contains nothing of note."
        return embed

    # Equipped Gear
    if categories["Equipped"]:
        embed.add_field(
            name="Equipped Gear",
            value="```ansi\n" + "\n".join(categories["Equipped"]) + "\n```",
            inline=False,
        )

    # Render other categories following standard Eldoria UX ordering
    for cat in ["Equipment", "Consumable", "Material", "Misc"]:
        if cat in categories and categories[cat]:
            embed.add_field(
                name=cat,
                value="```ansi\n" + "\n".join(categories[cat]) + "\n```",
                inline=False,
            )

    return embed


# ======================================================================
# NAVIGATION CALLBACKS
# ======================================================================

async def back_to_profile_callback(
    interaction: discord.Interaction, is_new_message: bool = False
):
    """
    Return to the Character Status screen — the adventurer's
    personal profile recognized by the Guild.

    This serves as the 'home' of the player UI.
    """
    from game_systems.character.ui.profile_view import CharacterTabView

    if not interaction.response.is_done():
        await interaction.response.defer()

    discord_id = interaction.user.id
    db = DatabaseManager()

    player = await asyncio.to_thread(db.get_player, discord_id)
    if not player:
        await interaction.followup.send(
            "Error: No character data found.", ephemeral=True
        )
        return

    # Fetch all dependent data in parallel for max responsiveness
    guild_data_task = asyncio.to_thread(db.get_guild_member_data, discord_id)
    stats_json_task = asyncio.to_thread(db.get_player_stats_json, discord_id)
    class_row_task = asyncio.to_thread(db.get_class, player["class_id"])
    player_skills_task = asyncio.to_thread(db.get_player_skills, discord_id)

    guild_data, stats_json, class_row, player_skills = await asyncio.gather(
        guild_data_task,
        stats_json_task,
        class_row_task,
        player_skills_task,
    )

    stats = PlayerStats.from_dict(stats_json)
    class_name = class_row["name"] if class_row else "Unknown"

    embed = discord.Embed(
        title=f"{E.SCROLL} {player['name']}'s Character Status",
        description=(
            f"**Occupation:** Adventurer\n"
            f"**Class:** {class_name}"
        ),
        color=discord.Color.dark_red(),
    )

    if interaction.user.avatar:
        embed.set_thumbnail(url=interaction.user.avatar.url)

    embed.add_field(
        name="Condition",
        value=(
            f"**Lv.** {player['level']}\n"
            f"**Guild Rank:** {guild_data['rank'] if guild_data else 'Unregistered'}"
        ),
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

    # Skills
    if not player_skills:
        skills_str = "No skills acquired."
    else:
        active_skills = []
        passive_skills = []

        for s in player_skills:
            line = f"• **{s['name']}** (Lv. {s['skill_level']})"
            (active_skills if s["type"] == "Active" else passive_skills).append(line)

        combined = []
        if active_skills:
            combined.append("**Active Skills**\n" + "\n".join(active_skills))
        if passive_skills:
            combined.append("**Passive Skills**\n" + "\n".join(passive_skills))

        skills_str = "\n\n".join(combined)

    embed.add_field(name="Acquired Skills", value=skills_str, inline=False)

    view = CharacterTabView(db, interaction.user)

    if is_new_message:
        await interaction.followup.send(embed=embed, view=view)
    else:
        await interaction.edit_original_response(embed=embed, view=view)


async def back_to_guild_hall_callback(interaction: discord.Interaction):
    """
    Return to the Adventurer's Guild Hall — the primary hub for quests,
    services, and advancement.
    """
    from game_systems.guild_system.ui.lobby_view import GuildLobbyView

    if not interaction.response.is_done():
        await interaction.response.defer()

    discord_id = interaction.user.id
    db = DatabaseManager()

    card_data = await asyncio.to_thread(db.get_guild_card_data, discord_id)
    if not card_data:
        await interaction.edit_original_response(
            content="Error: Guild data not found.",
            embed=None,
            view=None,
        )
        return

    embed = discord.Embed(
        title="🏰 Adventurer’s Guild Hall",
        description=(
            "*The receptionist inspects your guild card, offering a polite bow.*\n\n"
            f"**{card_data['name']} — Rank {card_data['rank']}**\n"
            "“How may the Guild assist you today?”"
        ),
        color=discord.Color.dark_gold(),
    )

    embed.add_field(
        name="📜 Quest Board",
        value=(
            "• **Available Quests** — Browse open missions\n"
            "• **Current Progress** — Track your active assignments\n"
            "• **Rank Trials** — Attempt advancement challenges"
        ),
        inline=False,
    )

    embed.add_field(
        name="⚙️ Guild Services",
        value=(
            "• **Guild Shop** — Purchase arms, supplies, and essentials\n"
            "• **Item Exchange** — Trade materials and rare loot\n"
            "• **Facilities** — Access training grounds and workshops"
        ),
        inline=False,
    )

    embed.set_footer(text="Select an option below.")

    view = GuildLobbyView(db, interaction.user)
    await interaction.edit_original_response(embed=embed, view=view)
