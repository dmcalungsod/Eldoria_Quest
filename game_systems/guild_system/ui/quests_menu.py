"""
game_systems/guild_system/ui/quests_menu.py
Sub-menu for quest operations.
Hardened: Async processing and safe JSON data handling.
"""

import asyncio
import logging

import discord
from discord.ui import Button, View

import game_systems.data.emojis as E
from cogs.ui_helpers import back_to_guild_hall_callback, make_progress_bar
from database.database_manager import DatabaseManager
from game_systems.guild_system.quest_system import QuestSystem

from .components import EmbedBuilder, GuildViewMixin, SystemCache, ViewFactory
from .rank_view import RankProgressView

logger = logging.getLogger("eldoria.ui.quests")


class QuestsMenuView(View, GuildViewMixin):
    """
    Main interface for the Adventurer's Guild quest-related systems.
    Handles available quests, active quests, quest turn-ins, and rank progress.
    """

    def __init__(self, db_manager: DatabaseManager, interaction_user: discord.User):
        super().__init__(timeout=180)
        self.db = db_manager
        self.interaction_user = interaction_user
        self.rank_system = SystemCache.get_rank_system(db_manager)

        # Core Guild Buttons
        self.add_item(
            ViewFactory.create_button(
                "Quest Board",
                discord.ButtonStyle.primary,
                "g_q_board",
                E.SCROLL,
                0,
                callback=self.view_quests_callback,
            )
        )
        self.add_item(
            ViewFactory.create_button(
                "Quest Ledger",
                discord.ButtonStyle.primary,
                "g_q_ledger",
                E.QUEST_SCROLL,
                0,
                callback=self.view_quest_ledger_callback,
            )
        )
        self.add_item(
            ViewFactory.create_button(
                "Turn-In",
                discord.ButtonStyle.success,
                "g_turn_in",
                E.MEDAL,
                0,
                callback=self.quest_turn_in_callback,
            )
        )
        self.add_item(
            ViewFactory.create_button(
                "Rank Evaluation",
                discord.ButtonStyle.secondary,
                "g_check_rank",
                "🏅",
                1,
                callback=self.check_rank_callback,
            )
        )

        self.back_btn = ViewFactory.create_button(
            "Back to Guild Lobby",
            discord.ButtonStyle.grey,
            "back_lobby",
            row=1,
            callback=back_to_guild_hall_callback,
        )
        self.add_item(self.back_btn)

    # ------------------------------
    # Quest Board
    # ------------------------------
    async def view_quests_callback(self, interaction: discord.Interaction, button: Button = None):
        from cogs.quest_hub_cog import QuestBoardView

        await interaction.response.defer()

        quest_system = QuestSystem(self.db)
        quests = await asyncio.to_thread(quest_system.get_available_quests, self.interaction_user.id)

        # --- Narrative Update ---
        embed = discord.Embed(
            title=f"{E.SCROLL} Quest Board",
            description="The board is pinned with desperate pleas and official warrants. Choose your burden.",
            color=discord.Color.dark_green(),
        )
        embed.add_field(
            name="Available Contracts",
            value="Select a quest from the dropdown below.",
            inline=False,
        )

        view = QuestBoardView(self.db, quests, self.interaction_user)
        view.set_back_button(self.back_to_this_menu, "Back to Quests")
        await interaction.edit_original_response(embed=embed, view=view)

    # ------------------------------
    # Quest Ledger
    # ------------------------------
    async def view_quest_ledger_callback(self, interaction: discord.Interaction, button: Button = None):
        from cogs.quest_hub_cog import QuestLedgerView

        await interaction.response.defer()

        quest_system = QuestSystem(self.db)
        quests = await asyncio.to_thread(quest_system.get_player_quests, self.interaction_user.id)

        # --- Narrative Update ---
        embed = discord.Embed(
            title=f"{E.QUEST_SCROLL} Quest Ledger",
            description="The oaths you have sworn to the Guild. Leave none unfulfilled.",
            color=discord.Color.from_rgb(139, 69, 19),
        )

        if not quests:
            embed.add_field(
                name="No Active Contracts",
                value="Your ledger is empty. The Guild has need of you—consult the board.",
            )
        else:
            for q in quests:
                progress = self._format_progress(q)
                embed.add_field(
                    name=q["title"],
                    value="\n".join(progress) or "No objectives.",
                    inline=False,
                )

        view = QuestLedgerView(self.db, quests, self.interaction_user)
        view.set_back_button(self.back_to_this_menu, "Back to Quests")
        await interaction.edit_original_response(embed=embed, view=view)

    # ------------------------------
    # Quest Turn-In
    # ------------------------------
    async def quest_turn_in_callback(self, interaction: discord.Interaction, button: Button = None):
        from cogs.quest_hub_cog import QuestLogView

        await interaction.response.defer()

        quest_system = QuestSystem(self.db)
        quests = await asyncio.to_thread(quest_system.get_player_quests, self.interaction_user.id)

        # Check for completable quests
        completable_quests = [
            q for q in quests if quest_system.check_completion(q.get("progress", {}), q.get("objectives", {}))
        ]

        # --- Narrative Update ---
        embed = discord.Embed(
            title=f"{E.MEDAL} Quest Turn-In",
            description="Present your findings to the Guildmaster. Only success is rewarded here.",
            color=discord.Color.gold(),
        )

        if not quests:
            embed.add_field(
                name="No Active Contracts",
                value="You have no completed contracts to report. Return when the work is done.",
            )
        elif not completable_quests:
            embed.description = "*The Guildmaster reviews your report and shakes his head.*\n\n“You have not met the requirements, Adventurer. Return when the work is done.”"
            embed.color = discord.Color.orange()

            # Show progress for active quests so they know what's missing
            for q in quests:
                progress = self._format_progress(q)
                embed.add_field(
                    name=f"⏳ {q['title']} (In Progress)",
                    value="\n".join(progress) or "No objectives.",
                    inline=False,
                )

        view = QuestLogView(self.db, quests, self.interaction_user)
        view.set_back_button(self.back_to_this_menu, "Back to Quests")
        await interaction.edit_original_response(embed=embed, view=view)

    # ------------------------------
    # Rank Evaluation
    # ------------------------------
    async def check_rank_callback(self, interaction: discord.Interaction, button: Button = None):
        await interaction.response.defer()

        try:
            data = await asyncio.to_thread(self.rank_system.get_rank_info, self.interaction_user.id)
            if not data:
                await interaction.followup.send("Error fetching rank data.", ephemeral=True)
                return

            cur_rank = data.get("rank", "F")
            next_rank = self.rank_system.RANKS.get(cur_rank, {}).get("next_rank")

            # Max Rank
            if not next_rank:
                embed = discord.Embed(
                    title="Rank Evaluation",
                    description="You stand at the zenith of the Guild's hierarchy. There are no titles left to grant you.",
                    color=discord.Color.gold(),
                )
                view = RankProgressView(self.db, False, self.interaction_user)

            else:
                reqs = self.rank_system.RANKS[cur_rank].get("requirements", {})
                eligible = True
                lines = []

                for key, required in reqs.items():
                    current = data.get(key, 0)
                    bar = make_progress_bar(current, required, length=8)
                    lines.append(f"• {key.replace('_', ' ').title()}: `{bar}` {current}/{required}")
                    if current < required:
                        eligible = False

                embed = discord.Embed(
                    title=f"Rank Evaluation: {cur_rank} → {next_rank}",
                    color=discord.Color.blue(),
                )
                embed.add_field(name="Requirements", value="\n".join(lines))

                view = RankProgressView(self.db, eligible, self.interaction_user)

            view.set_back_button(self.back_to_this_menu, "Back to Quests")
            await interaction.edit_original_response(embed=embed, view=view)

        except Exception as e:
            logger.error(f"Rank check error for {self.interaction_user.id}: {e}", exc_info=True)
            await interaction.followup.send("An error occurred checking rank status.", ephemeral=True)

    # ------------------------------
    # Return to Menu
    # ------------------------------
    async def back_to_this_menu(self, interaction: discord.Interaction):
        await interaction.response.defer()
        view = QuestsMenuView(self.db, self.interaction_user)
        await interaction.edit_original_response(embed=EmbedBuilder.quest_menu(), view=view)

    # ------------------------------
    # Helper: Format Quest Progress
    # ------------------------------
    @staticmethod
    def _format_progress(quest):
        lines = []
        objs = quest.get("objectives", {})
        prog = quest.get("progress", {})

        for obj_type, tasks in objs.items():
            if isinstance(tasks, dict):
                for task, required in tasks.items():
                    cur = prog.get(obj_type, {}).get(task, 0)
                    bar = make_progress_bar(cur, required, length=8)
                    lines.append(f"• {task}: `{bar}` {cur}/{required}")
            else:
                cur = prog.get(obj_type, {}).get(tasks, 0)
                bar = make_progress_bar(cur, 1, length=8)
                lines.append(f"• {obj_type.title()} {tasks}: `{bar}` {cur}/1")

        return lines
