"""
cogs/quest_hub_cog.py

Handles all UI Views related to the Questing System:
- Quest Board (available quests)
- Quest Ledger (active quests, read-only)
- Quest Log (turn-in)
- Quest Detail (viewing and accepting)

Refactored to strictly adhere to ONE UI Policy and fix navigation crashes.
Hardened with atomic status checks and concurrency protection.
"""

import asyncio
import logging

import discord
from discord.ext import commands
from discord.ui import Button, Select, View

import game_systems.data.emojis as E
from database.database_manager import DatabaseManager
from game_systems.guild_system.quest_system import QuestSystem

# --- Local Imports ---
from .ui_helpers import back_to_guild_hall_callback, back_to_profile_callback

logger = logging.getLogger("eldoria.quest_ui")


# ======================================================================
# QUEST LEDGER VIEW (READ-ONLY)
# ======================================================================


class QuestLedgerView(View):
    """
    Displays the player's currently accepted quests.
    This is read-only and does not allow turn-in.
    """

    def __init__(self, db_manager: DatabaseManager, active_quests: list, interaction_user: discord.User):
        super().__init__(timeout=180)
        self.db = db_manager
        self.active_quests = active_quests
        self.interaction_user = interaction_user

        # Back Button
        self.back_button = Button(
            label="Back to Guild Hall",
            style=discord.ButtonStyle.secondary,
            custom_id="back_to_guild_hall",
            row=1,
        )
        self.back_button.callback = back_to_guild_hall_callback
        self.add_item(self.back_button)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.interaction_user.id:
            await interaction.response.send_message("This is not your adventure.", ephemeral=True)
            return False
        return True

    def set_back_button(self, callback_function, label="Back"):
        """Allows parent menus to override the back button destination."""
        self.back_button.label = label
        self.back_button.callback = callback_function


# ======================================================================
# QUEST LOG (TURN-IN VIEW)
# ======================================================================


class QuestLogView(View):
    """
    Displays accepted quests and allows the player to turn in completed ones.
    """

    def __init__(self, db_manager: DatabaseManager, active_quests: list, interaction_user: discord.User):
        super().__init__(timeout=180)
        self.db = db_manager
        self.active_quests = active_quests
        self.interaction_user = interaction_user
        self.quest_system = QuestSystem(self.db)

        # Back Button
        self.back_button = Button(
            label="Back to Profile",
            style=discord.ButtonStyle.secondary,
            custom_id="back_to_profile",
            row=1,
        )
        self.back_button.callback = back_to_profile_callback
        self.add_item(self.back_button)

        # Quest dropdown (turn-in)
        self.quest_select = Select(
            placeholder="Report a completed quest...",
            min_values=1,
            max_values=1,
            row=0,
        )

        # Determine completable quests synchronously
        completable_quests = []
        for quest in self.active_quests:
            # Uses logic from QuestSystem to check progress vs objectives
            if self.quest_system.check_completion(quest["progress"], quest["objectives"]):
                completable_quests.append(quest)

        if not completable_quests:
            self.quest_select.add_option(
                label="No quests are ready for turn-in.",
                value="disabled",
                emoji=E.ERROR,
            )
            self.quest_select.disabled = True
        else:
            for quest in completable_quests:
                self.quest_select.add_option(
                    label=f"Turn In: {quest['title']}",
                    value=str(quest["id"]),
                    emoji=E.MEDAL,
                )

        self.quest_select.callback = self.complete_quest_callback
        self.add_item(self.quest_select)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.interaction_user.id:
            await interaction.response.send_message("This is not your adventure.", ephemeral=True)
            return False
        return True

    def set_back_button(self, callback_function, label="Back"):
        self.back_button.label = label
        self.back_button.callback = callback_function

    async def complete_quest_callback(self, interaction: discord.Interaction):
        """
        Handles the turn-in logic.
        Uses asyncio.to_thread to prevent blocking during DB writes.
        """
        await interaction.response.defer()

        try:
            quest_id = int(self.quest_select.values[0])
        except (ValueError, IndexError):
            await interaction.followup.send("Invalid selection.", ephemeral=True)
            return

        # Execute completion logic in thread
        success, message = await asyncio.to_thread(
            self.quest_system.complete_quest,
            self.interaction_user.id,
            quest_id,
        )

        # Refresh quest list to show updated state
        new_active_quests = await asyncio.to_thread(self.quest_system.get_player_quests, self.interaction_user.id)

        # Rebuild the embed
        embed = interaction.message.embeds[0]
        embed.description = message
        embed.clear_fields()

        if not new_active_quests:
            embed.add_field(name="No Active Quests", value="Visit the Quest Board to accept a task.")
        else:
            for quest in new_active_quests:
                progress_lines = []
                objectives = quest.get("objectives", {})
                progress = quest.get("progress", {})

                for obj_type, tasks in objectives.items():
                    if isinstance(tasks, dict):
                        for task, req in tasks.items():
                            cur = progress.get(obj_type, {}).get(task, 0)
                            progress_lines.append(f"• {task}: {cur}/{req}")
                    else:
                        task = tasks
                        cur = progress.get(obj_type, {}).get(task, 0)
                        progress_lines.append(f"• {obj_type.title()} {task}: {cur}/1")

                embed.add_field(
                    name=f"{quest['title']} (ID: {quest['id']})",
                    value="\n".join(progress_lines) or "No objectives.",
                    inline=False,
                )

        if not success:
            embed.color = discord.Color.red()
            embed.title = f"{E.ERROR} Turn-In Rejected"
        else:
            embed.color = discord.Color.gold()
            # Log success
            logger.info(f"User {self.interaction_user.id} completed quest {quest_id}")

        # Show updated view
        new_view = QuestLogView(self.db, new_active_quests, self.interaction_user)
        new_view.set_back_button(self.back_button.callback, self.back_button.label)

        await interaction.edit_original_response(embed=embed, view=new_view)


# ======================================================================
# QUEST BOARD VIEW
# ======================================================================


class QuestBoardView(View):
    """
    Displays all available quests in a dropdown list.
    """

    def __init__(
        self,
        db_manager: DatabaseManager,
        quests: list,
        interaction_user: discord.User,
        status_message: str = None,
        parent_back_data: tuple = None,
    ):
        super().__init__(timeout=180)
        self.db = db_manager
        self.quests = quests
        self.interaction_user = interaction_user
        self.quest_system = QuestSystem(self.db)
        self.status_message = status_message

        # Store navigation context (Callback, Label)
        self.parent_back_data = parent_back_data

        # --- Quest Select ---
        self.quest_select = Select(
            placeholder="Select a guild contract...",
            min_values=1,
            max_values=1,
        )

        if not self.quests:
            self.quest_select.add_option(
                label="No quests available.",
                value="disabled",
                emoji=E.ERROR,
            )
            self.quest_select.disabled = True
        else:
            # Limit to 25 options (Discord API limit)
            for quest in self.quests[:25]:
                self.quest_select.add_option(
                    label=f"[{quest['tier']}-Rank] {quest['title']}",
                    description=quest["summary"][:100],
                    value=str(quest["id"]),
                    emoji=E.HERB,
                )

        self.quest_select.callback = self.view_quest_details_callback
        self.add_item(self.quest_select)

        # --- Back Button ---
        self.back_button = Button(
            label="Back to Guild Hall",
            style=discord.ButtonStyle.secondary,
            custom_id="back_to_guild_hall",
        )

        # Apply parent context if it exists (persisting navigation)
        if self.parent_back_data:
            self.back_button.callback = self.parent_back_data[0]
            self.back_button.label = self.parent_back_data[1]
        else:
            self.back_button.callback = back_to_guild_hall_callback

        self.add_item(self.back_button)

    def set_back_button(self, callback_function, label="Back"):
        """Allows external callers to change where the back button goes."""
        self.back_button.label = label
        self.back_button.callback = callback_function
        # Save this so we can pass it to child views
        self.parent_back_data = (callback_function, label)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.interaction_user.id:
            await interaction.response.send_message("This is not your adventure.", ephemeral=True)
            return False
        return True

    async def view_quest_details_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()

        try:
            quest_id = int(self.quest_select.values[0])
        except (ValueError, IndexError):
            await self.refresh_board(interaction, f"{E.ERROR} Invalid quest selection.")
            return

        quest_details = await asyncio.to_thread(self.quest_system.get_quest_details, quest_id)

        if not quest_details:
            await self.refresh_board(interaction, f"{E.ERROR} Could not retrieve quest details.")
            return

        embed = discord.Embed(
            title=f"{E.HERB} Quest: {quest_details['title']}",
            description=quest_details["description"],
            color=discord.Color.dark_teal(),
        )

        # Objectives
        obj_lines = []
        for obj_type, tasks in quest_details.get("objectives", {}).items():
            if isinstance(tasks, dict):
                for task, amt in tasks.items():
                    obj_lines.append(f"• **{obj_type.title()}:** {task} ({amt})")
            else:
                # Fallback for simple string tasks
                obj_lines.append(f"• **{obj_type.title()}:** {tasks}")

        embed.add_field(
            name="Objectives",
            value="\n".join(obj_lines) or "No objectives listed.",
            inline=False,
        )

        # Rewards
        reward_lines = []
        for reward, value in quest_details.get("rewards", {}).items():
            label = "Aurum" if reward == "aurum" else reward.title()
            reward_lines.append(f"• **{label}:** {value}")

        embed.add_field(
            name="Rewards",
            value="\n".join(reward_lines) or "No rewards listed.",
            inline=False,
        )
        embed.set_footer(text=f"Quest ID: {quest_id} | Tier: {quest_details['tier']}")

        # Pass navigation context to Detail View
        view = QuestDetailView(
            self.db, quest_id, self.quests, self.interaction_user, parent_back_data=self.parent_back_data
        )
        await interaction.edit_original_response(embed=embed, view=view)

    async def refresh_board(self, interaction: discord.Interaction, status_msg: str = None):
        """Helper to reload the board with a status message."""
        quests = await asyncio.to_thread(self.quest_system.get_available_quests, self.interaction_user.id)

        embed = discord.Embed(
            title=f"{E.SCROLL} Quest Board",
            description="The board is cluttered with parchment requests and sealed contracts.",
            color=discord.Color.dark_green(),
        )

        if status_msg:
            embed.add_field(name="Update", value=status_msg, inline=False)

        embed.add_field(
            name="Available Contracts",
            value="Select a quest from the dropdown.",
        )

        # Pass navigation context back
        view = QuestBoardView(
            self.db, quests, self.interaction_user, status_message=status_msg, parent_back_data=self.parent_back_data
        )
        await interaction.edit_original_response(embed=embed, view=view)


# ======================================================================
# QUEST DETAIL VIEW
# ======================================================================


class QuestDetailView(View):
    """
    Displays full details for a specific quest and allows acceptance.
    """

    def __init__(
        self,
        db_manager: DatabaseManager,
        quest_id: int,
        quests_list: list,
        interaction_user: discord.User,
        parent_back_data: tuple = None,
    ):
        super().__init__(timeout=180)
        self.db = db_manager
        self.quest_id = quest_id
        self.quests_list = quests_list
        self.interaction_user = interaction_user
        self.quest_system = QuestSystem(self.db)

        # Store navigation to return to the correct board state
        self.parent_back_data = parent_back_data

        accept_button = Button(
            label="Accept Quest",
            style=discord.ButtonStyle.success,
            custom_id=f"accept_quest_{self.quest_id}",
        )
        accept_button.callback = self.accept_quest_callback
        self.add_item(accept_button)

        back_button = Button(
            label="Back to Quest Board",
            style=discord.ButtonStyle.secondary,
            custom_id="back_to_quest_board",
        )
        back_button.callback = self.back_to_quest_board_callback
        self.add_item(back_button)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.interaction_user.id:
            await interaction.response.send_message("This is not your adventure.", ephemeral=True)
            return False
        return True

    async def accept_quest_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()

        # Perform atomic acceptance
        success = await asyncio.to_thread(
            self.quest_system.accept_quest,
            self.interaction_user.id,
            self.quest_id,
        )

        status_msg = ""
        if success:
            status_msg = f"{E.CHECK} Contract sealed. The details are recorded in your ledger."
            logger.info(f"User {self.interaction_user.id} accepted quest {self.quest_id}")
        else:
            status_msg = f"{E.WARNING} You have already sworn to undertake this task."

        await self.back_to_quest_board_callback(interaction, deferred=True, status_message=status_msg)

    async def back_to_quest_board_callback(
        self, interaction: discord.Interaction, deferred: bool = False, status_message: str = None
    ):
        if not deferred and not interaction.response.is_done():
            await interaction.response.defer()

        available_quests = await asyncio.to_thread(
            self.quest_system.get_available_quests,
            self.interaction_user.id,
        )

        embed = discord.Embed(
            title=f"{E.SCROLL} Quest Board",
            description="The board is cluttered with parchment requests and sealed contracts.",
            color=discord.Color.dark_green(),
        )

        if status_message:
            embed.add_field(name="Update", value=status_message, inline=False)

        embed.add_field(
            name="Available Contracts",
            value="Select a quest from the dropdown.",
        )

        # Restore the Board View with the original navigation context
        view = QuestBoardView(
            self.db,
            available_quests,
            self.interaction_user,
            status_message=status_message,
            parent_back_data=self.parent_back_data,
        )
        await interaction.edit_original_response(embed=embed, view=view)


# ======================================================================
# COG LOADER
# ======================================================================


class QuestHubCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = DatabaseManager()


async def setup(bot: commands.Bot):
    await bot.add_cog(QuestHubCog(bot))
