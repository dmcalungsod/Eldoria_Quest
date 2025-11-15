"""
guild_hub_cog.py
... (imports and GuildCardView) ...
"""

import json
import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Button

from database.database_manager import DatabaseManager
from game_systems.guild_system.rank_system import RankSystem
from game_systems.guild_system.guild_exchange import GuildExchange
from game_systems.player.player_stats import PlayerStats
from game_systems.items.inventory_manager import InventoryManager
import game_systems.data.emojis as E

# --- Local Imports ---
from .ui_helpers import back_to_guild_card_callback

# We import the Quest views from the other cog for the button callback
from .quest_hub_cog import QuestBoardView, QuestLogView

# --- Adventure View Import ---
from .adventure_commands import AdventureSetupView


# ======================================================================
# GUILD CARD & MAIN MENU
# ======================================================================


class GuildCardView(View):
    """
    The view for the player's Guild Card, showing main actions.
    This is the "Main Menu" of the Guild Hall.
    """

    def __init__(self, db_manager: DatabaseManager):
        super().__init__(timeout=None)
        self.db = db_manager
        self.rank_system = RankSystem(self.db)
        self.inventory_manager = InventoryManager(self.db)

        # --- Row 1: Primary Actions ---
        quests_button = Button(
            label="Quest Board",
            style=discord.ButtonStyle.primary,
            custom_id="view_quests",
            emoji=E.HERB,
        )
        quests_button.callback = self.view_quests_callback
        self.add_item(quests_button)

        quest_log_button = Button(
            label="Quest Log",
            style=discord.ButtonStyle.primary,
            custom_id="view_quest_log",
            emoji=E.QUEST_SCROLL,
        )
        quest_log_button.callback = self.view_quest_log_callback
        self.add_item(quest_log_button)

        exchange_button = Button(
            label="Guild Exchange",
            style=discord.ButtonStyle.primary,
            custom_id="guild_exchange",
            emoji=E.EXCHANGE,
        )
        exchange_button.callback = self.guild_exchange_callback
        self.add_item(exchange_button)

        # --- Row 2: Character Management ---
        profile_button = Button(
            label="View Profile",
            style=discord.ButtonStyle.secondary,
            custom_id="view_profile",
            emoji=E.SCROLL,
        )
        profile_button.callback = self.view_profile_callback
        self.add_item(profile_button)

        inventory_button = Button(
            label="Inventory",
            style=discord.ButtonStyle.secondary,
            custom_id="view_inventory",
            emoji=E.BACKPACK,
        )
        inventory_button.callback = self.view_inventory_callback
        self.add_item(inventory_button)

        check_rank_button = Button(
            label="Check Rank",
            style=discord.ButtonStyle.secondary,
            custom_id="check_rank",
            emoji=E.MEDAL,
        )
        check_rank_button.callback = self.check_rank_callback
        self.add_item(check_rank_button)

    async def view_quests_callback(self, interaction: discord.Interaction):
        """
        Hands off to the QuestBoardView from the quest_hub_cog.
        """
        await interaction.response.defer()
        from game_systems.guild_system.quest_system import QuestSystem

        quest_system = QuestSystem(self.db)

        available_quests = quest_system.get_available_quests(interaction.user.id)

        embed = discord.Embed(
            title=f"{E.SCROLL} Quest Board",
            description="The board is cluttered with parchment sheets—some crisp and new, others curled and water-stained. The scent of pine resin clings to them.",
            color=discord.Color.dark_green(),
        )

        if not available_quests:
            embed.add_field(
                name="No Quests Available",
                value="There are currently no quests available for your rank. Check back later, adventurer.",
            )
        else:
            embed.add_field(
                name="Available Contracts",
                value="Select an available quest from the dropdown menu to review its details.",
            )

        view = QuestBoardView(self.db, available_quests)
        await interaction.edit_original_response(embed=embed, view=view)

    async def view_quest_log_callback(self, interaction: discord.Interaction):
        """
        Hands off to the QuestLogView from the quest_hub_cog.
        """
        await interaction.response.defer()
        from game_systems.guild_system.quest_system import QuestSystem

        quest_system = QuestSystem(self.db)

        active_quests = quest_system.get_player_quests(interaction.user.id)

        embed = discord.Embed(
            title=f"{E.QUEST_SCROLL} Adventurer's Log",
            description="A review of your currently accepted assignments from the Guild.",
            color=discord.Color.from_rgb(139, 69, 19),  # Brown
        )

        if not active_quests:
            embed.add_field(
                name="No Active Quests",
                value="You have no assignments. Please visit the Quest Board to accept a new task.",
            )
        else:
            for quest in active_quests:
                progress_text = []
                objectives = quest.get("objectives", {})
                progress = quest.get("progress", {})

                for obj_type, tasks in objectives.items():
                    if isinstance(tasks, dict):
                        for task, required in tasks.items():
                            current = progress.get(obj_type, {}).get(task, 0)
                            progress_text.append(f"• {task}: {current} / {required}")
                    else:
                        current = progress.get(obj_type, {}).get(tasks, 0)
                        progress_text.append(f"• {tasks}: {current} / 1")

                embed.add_field(
                    name=f"{quest['title']} (ID: {quest['id']})",
                    value=(
                        "\n".join(progress_text) if progress_text else "No objectives."
                    ),
                    inline=False,
                )

        view = QuestLogView(self.db, active_quests, interaction.user.id)

        await interaction.edit_original_response(embed=embed, view=view)

    async def guild_exchange_callback(self, interaction: discord.Interaction):
        """
        Switches to the Guild Exchange view.
        """
        await interaction.response.defer()

        exchange = GuildExchange(self.db)
        total_value, materials = exchange.calculate_exchange_value(interaction.user.id)

        embed = discord.Embed(
            title=f"{E.EXCHANGE} Guild Exchange",
            description=f'A guild receptionist looks up from her ledger. "Greetings, adventurer. Here to exchange your haul for Aurum?"\n\nShe tallies your materials...',
            color=discord.Color.blue(),
        )

        if total_value == 0:
            embed.add_field(
                name="Materials on Hand", value="You have no materials to exchange."
            )
        else:
            mat_list = [f"• {item['item_name']} x{item['count']}" for item in materials]
            embed.add_field(
                name="Materials on Hand", value="\n".join(mat_list), inline=False
            )
            embed.add_field(
                name="Total Value",
                value=f"{E.AURUM} **{total_value} Aurum**",
                inline=False,
            )

        view = GuildExchangeView(self.db, total_value > 0)
        await interaction.edit_original_response(embed=embed, view=view)

    async def view_profile_callback(self, interaction: discord.Interaction):
        """
        Displays the player's profile/status.
        This screen is now ALSO the hub for adventure actions.
        """
        await interaction.response.defer()
        discord_id = interaction.user.id
        player = self.db.get_player(discord_id)

        if not player:
            await interaction.edit_original_response(
                content="Could not find your player data.", embed=None, view=None
            )
            return

        conn = self.db.connect()
        cur = conn.cursor()
        cur.execute(
            "SELECT rank, merit_points FROM guild_members WHERE discord_id = ?",
            (discord_id,),
        )
        guild_data = cur.fetchone()
        conn.close()

        stats_json = self.db.get_player_stats_json(discord_id)
        stats = PlayerStats.from_dict(stats_json)
        class_row = self.db.get_class(player["class_id"])
        class_name = class_row["name"] if class_row else "Unknown"

        embed = discord.Embed(
            title=f"{E.SCROLL} Adventurer Status — {player['name']}",
            description=f"**Guild:** Adventurer's Guild\n**Class:** {class_name}",
            color=discord.Color.dark_red(),
        )
        embed.set_thumbnail(
            url=interaction.user.avatar.url if interaction.user.avatar else None
        )
        embed.add_field(
            name="Condition",
            value=f"**Lv.** {player['level']}\n**Rank:** {guild_data['rank']}",
            inline=True,
        )
        embed.add_field(
            name="Progress",
            value=f"**EXP:** {player['experience']} / {player['exp_to_next']}\n**Merit:** {guild_data['merit_points']}",
            inline=True,
        )

        stat_block = (
            f"`STR: {stats.strength:<3}` `END: {stats.endurance:<3}` `DEX: {stats.dexterity:<3}`\n"
            f"`AGI: {stats.agility:<3}` `MAG: {stats.magic:<3}` `LCK: {stats.luck:<3}`"
        )
        embed.add_field(name="Basic Abilities", value=stat_block, inline=False)

        embed.add_field(
            name="Vitals",
            value=f"{E.HP} **HP:** {stats.max_hp}\n{E.MP} **MP:** {stats.max_mp}",
            inline=True,
        )
        embed.add_field(
            name="Wealth",
            value=f"{E.AURUM} **Aurum:** {player['aurum']}",
            inline=True,
        )

        # --- NEW SKILLS FIELD ---
        player_skills = self.db.get_player_skills(discord_id)
        if not player_skills:
            skills_str = "You have not learned any skills."
        else:
            skills_str = "\n".join(
                [
                    f"• **{s['name']}** (Lv. {s['skill_level']}) - *{s['type']}*"
                    for s in player_skills
                ]
            )

        embed.add_field(name="Acquired Skills", value=skills_str, inline=False)
        # --- END NEW FIELD ---

        embed.set_footer(text="Your status is a record of your journey and strength.")

        view = ProfileView(self.db, interaction.client, discord_id)
        await interaction.edit_original_response(embed=embed, view=view)

    async def view_inventory_callback(self, interaction: discord.Interaction):
        """
        Displays the player's inventory as an ephemeral message.
        """
        items = self.inventory_manager.get_inventory(interaction.user.id)

        if not items:
            await interaction.response.send_message(
                f"{E.BACKPACK} Your backpack is empty.", ephemeral=True
            )
            return

        embed = discord.Embed(
            title=f"{E.BACKPACK} Backpack", color=discord.Color.brown()
        )

        categories = {}
        for item in items:
            itype = item["item_type"].title()
            if itype not in categories:
                categories[itype] = []
            categories[itype].append(f"• {item['item_name']} (x{item['count']})")

        for category, item_list in categories.items():
            embed.add_field(name=category, value="\n".join(item_list), inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)

    async def check_rank_callback(self, interaction: discord.Interaction):
        """
        Checks player's promotion eligibility and switches to the Rank Progress view.
        """
        await interaction.response.defer()
        discord_id = interaction.user.id
        player_data = self.rank_system.get_rank_info(discord_id)

        if not player_data:
            await interaction.edit_original_response(
                content="Could not retrieve your guild data.", embed=None, view=None
            )
            return

        current_rank = player_data["rank"]
        next_rank_key = self.rank_system.RANKS.get(current_rank, {}).get("next_rank")

        if not next_rank_key:
            embed = discord.Embed(
                title=f"{E.MEDAL} Rank Status: {current_rank}",
                description="You have already reached the highest available rank. Your legend is known throughout the Guild.",
                color=discord.Color.gold(),
            )
            view = RankProgressView(self.db, eligible=False)
            await interaction.edit_original_response(embed=embed, view=view)
            return

        requirements = self.rank_system.RANKS[current_rank].get("requirements", {})
        next_rank_title = self.rank_system.RANKS[next_rank_key]["title"]

        embed = discord.Embed(
            title=f"{E.MEDAL} Promotion Evaluation: Rank {current_rank} → Rank {next_rank_key}",
            description=f"Here is your progress towards the rank of **{next_rank_title}**.",
            color=discord.Color.blue(),
        )

        progress_text = ""
        eligible = True
        for req, required_value in requirements.items():
            current_value = player_data.get(req, 0)
            progress_text += f"• **{req.replace('_', ' ').title()}:** {current_value} / {required_value}\n"
            if current_value < required_value:
                eligible = False

        embed.add_field(name="Current Progress", value=progress_text, inline=False)

        if eligible:
            embed.color = discord.Color.green()
            embed.set_footer(
                text="You are eligible for promotion! Speak with the Guild Master."
            )
        else:
            embed.set_footer(text="Continue your efforts, adventurer.")

        view = RankProgressView(self.db, eligible=eligible)
        await interaction.edit_original_response(embed=embed, view=view)


# ======================================================================
# PROFILE VIEW (NOW THE ADVENTURE HUB)
# ======================================================================


class ProfileView(View):
    """
    Shows the player's status and now handles adventure actions.
    """

    def __init__(self, db_manager: DatabaseManager, bot: commands.Bot, discord_id: int):
        super().__init__(timeout=None)
        self.db = db_manager
        self.bot = bot
        self.discord_id = discord_id

        adventure_cog = self.bot.get_cog("AdventureCommands")
        if not adventure_cog:
            self.manager = None
            is_active = True
        else:
            self.manager = adventure_cog.manager
            active_session = self.manager.get_active_session(self.discord_id)
            is_active = active_session and active_session["active"]

        start_button = Button(
            label="Start Adventure",
            style=discord.ButtonStyle.success,
            custom_id="profile_start_adv",
            emoji=E.MAP,
            disabled=is_active or (self.manager is None),
        )
        start_button.callback = self.start_adventure_callback
        self.add_item(start_button)

        status_button = Button(
            label="Check Status",
            style=discord.ButtonStyle.secondary,
            custom_id="profile_check_status",
            disabled=not is_active or (self.manager is None),
        )
        status_button.callback = self.check_status_callback
        self.add_item(status_button)

        cancel_button = Button(
            label="Return Early",
            style=discord.ButtonStyle.danger,
            custom_id="profile_cancel_adv",
            disabled=not is_active or (self.manager is None),
        )
        cancel_button.callback = self.cancel_adventure_callback
        self.add_item(cancel_button)

        back_button = Button(
            label="Back to Guild Card",
            style=discord.ButtonStyle.secondary,
            custom_id="back_to_guild_card",
            row=1,
        )
        back_button.callback = back_to_guild_card_callback
        self.add_item(back_button)

    async def start_adventure_callback(self, interaction: discord.Interaction):
        """
        Launches the adventure setup menu with an atmospheric embed.
        """
        if not self.manager:
            await interaction.response.send_message(
                f"{E.ERROR} Adventure system is offline.", ephemeral=True
            )
            return

        embed = discord.Embed(
            title=f"{E.MAP} Prepare for Expedition",
            description=(
                "You stand before the city gates, the Guild's clearance seal in your hand. "
                "The wilderness beyond the walls of Ashgrave awaits.\n\n"
                "Select a destination from the options below to begin your journey."
            ),
            color=discord.Color.dark_green(),
        )

        view = AdventureSetupView(self.db, self.manager)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    async def check_status_callback(self, interaction: discord.Interaction):
        """
        Shows the player's current adventure log.
        """
        if not self.manager:
            await interaction.response.send_message(
                f"{E.ERROR} Adventure system is offline.", ephemeral=True
            )
            return

        active_session = self.manager.get_active_session(self.discord_id)
        if not active_session or not active_session["active"]:
            await interaction.response.send_message(
                "You are not currently on an adventure.", ephemeral=True
            )
            return

        try:
            logs = json.loads(active_session["logs"])
            loot = json.loads(active_session["loot_collected"])
        except (json.JSONDecodeError, TypeError):
            logs = []
            loot = {}

        embed = discord.Embed(
            title=f"{E.QUEST_SCROLL} Adventure Log", color=discord.Color.green()
        )
        embed.description = "**Latest Events:**\n" + (
            "\n".join(logs[-5:]) if logs else "The journey begins..."
        )

        loot_str = ", ".join([f"{k} x{v}" for k, v in loot.items()])
        embed.add_field(name="Backpack", value=loot_str if loot_str else "Empty")

        await interaction.response.send_message(embed=embed, ephemeral=True)

    async def cancel_adventure_callback(self, interaction: discord.Interaction):
        """
        Cancels an ongoing adventure. (Placeholder)
        """
        if not self.manager:
            await interaction.response.send_message(
                f"{E.ERROR} Adventure system is offline.", ephemeral=True
            )
            return

        await interaction.response.send_message(
            "You signal for extraction. (Implementation pending)", ephemeral=True
        )


# ======================================================================
# RANK PROGRESS VIEW
# ======================================================================


class RankProgressView(View):
    """
    Shows the player's progress towards the next rank.
    Contains the "Promote" button.
    """

    def __init__(self, db_manager: DatabaseManager, eligible: bool):
        super().__init__(timeout=None)
        self.db = db_manager

        promote_button = Button(
            label="Request Promotion",
            style=discord.ButtonStyle.success,
            custom_id="promote",
            disabled=not eligible,
        )
        promote_button.callback = self.promote_callback
        self.add_item(promote_button)

        back_button = Button(
            label="Back to Guild Card",
            style=discord.ButtonStyle.secondary,
            custom_id="back_to_guild_card",
        )
        back_button.callback = back_to_guild_card_callback
        self.add_item(back_button)

    async def promote_callback(self, interaction: discord.Interaction):
        """
        Promotes the player to the next rank.
        """
        discord_id = interaction.user.id
        rank_system = RankSystem(self.db)
        success, message = rank_system.promote_player(discord_id)

        if success:
            await interaction.response.defer()
            await interaction.followup.send(message, ephemeral=True)
            await back_to_guild_card_callback(interaction)
        else:
            await interaction.response.send_message(message, ephemeral=True)


# ======================================================================
# GUILD EXCHANGE VIEW
# ======================================================================


class GuildExchangeView(View):
    """
    Handles the UI for selling materials.
    """

    def __init__(self, db_manager: DatabaseManager, can_sell: bool):
        super().__init__(timeout=None)
        self.db = db_manager

        sell_button = Button(
            label="Sell All Materials",
            style=discord.ButtonStyle.success,
            custom_id="sell_mats",
            disabled=not can_sell,
            emoji=E.AURUM,
        )
        sell_button.callback = self.sell_materials_callback
        self.add_item(sell_button)

        back_button = Button(
            label="Back to Guild Card",
            style=discord.ButtonStyle.secondary,
            custom_id="back_to_guild_card",
        )
        back_button.callback = back_to_guild_card_callback
        self.add_item(back_button)

    async def sell_materials_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()

        exchange = GuildExchange(self.db)
        total_earned, sold_items = exchange.exchange_all_materials(interaction.user.id)

        if total_earned == 0:
            await interaction.followup.send("You have nothing to sell.", ephemeral=True)
            return

        sold_list = [f"• {item['item_name']} x{item['count']}" for item in sold_items]

        receipt_embed = discord.Embed(
            title=f"{E.EXCHANGE} Exchange Complete",
            description=f'The receptionist stamps your ledger. "A fine haul, adventurer. Your payment has been processed."\n\n**Total Earned: {E.AURUM} {total_earned} Aurum**',
            color=discord.Color.green(),
        )
        receipt_embed.add_field(name="Sold Materials", value="\n".join(sold_list))

        await back_to_guild_card_callback(interaction, embed_to_show=receipt_embed)


# ======================================================================
# COG LOADER
# ======================================================================


class GuildHubCog(commands.Cog):
    """
    A cog for housing the main Guild Hub UI and its admin sub-views.
    This cog has no commands, it just makes the Views loadable
    and acts as the import hub for other UI cogs.
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = DatabaseManager()


async def setup(bot: commands.Bot):
    await bot.add_cog(GuildHubCog(bot))
