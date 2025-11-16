"""
quest_hub_cog.py

Handles all UI Views related to the Questing System:
- Quest Board (listing available)
- Quest Log (listing active)
- Quest Detail (viewing a single quest)
"""

import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Button, Select
import asyncio # <-- IMPORT ASYNCIO

from database.database_manager import DatabaseManager
from game_systems.guild_system.quest_system import QuestSystem
import game_systems.data.emojis as E

# --- Local Imports ---
from .ui_helpers import back_to_profile_callback, back_to_guild_hall_callback

# ======================================================================
# QUEST LEDGER VIEW (NEW)
# ======================================================================

class QuestLedgerView(View):
    """
    Displays the player's currently accepted quests (read-only).
    This is just for viewing, not completing.
    """

    def __init__(
        self,
        db_manager: DatabaseManager,
        active_quests: list,
        interaction_user: discord.User,
    ):
        super().__init__(timeout=None)
        self.db = db_manager
        self.active_quests = active_quests
        self.interaction_user = interaction_user

        # --- Back Button ---
        self.back_button = Button(
            label="Back to Quests Menu",
            style=discord.ButtonStyle.secondary,
            custom_id="back_to_guild_quests_menu", # This will be set by the parent
            row=1,
        )
        self.add_item(self.back_button)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.interaction_user.id:
            await interaction.response.send_message(
                "This is not your adventure.", ephemeral=True
            )
            return False
        return True

    def set_back_button(self, callback_function, label="Back"):
        self.back_button.label = label
        self.back_button.callback = callback_function


# ======================================================================
# QUEST LOG & TURN-IN VIEW
# ======================================================================


class QuestLogView(View):
    """
    Displays the player's currently accepted quests and allows completion.
    This is accessed from both the Profile and Guild Hall.
    """

    def __init__(
        self,
        db_manager: DatabaseManager,
        active_quests: list,
        interaction_user: discord.User,
    ):
        super().__init__(timeout=None)
        self.db = db_manager
        self.active_quests = active_quests
        self.interaction_user = interaction_user
        self.quest_system = QuestSystem(self.db)

        # --- Button 1: Back to Profile (Default) ---
        self.back_button = Button(
            label="Back to Profile",
            style=discord.ButtonStyle.secondary,
            custom_id="back_to_profile",
            row=1,
        )
        self.back_button.callback = back_to_profile_callback
        self.add_item(self.back_button)

        # --- Dropdown 1: Complete Quest ---
        self.quest_select = Select(
            placeholder="Report a completed quest...", min_values=1, max_values=1, row=0
        )
        
        # This is a blocking call, but it's in __init__
        completable_quests = []
        for quest in self.active_quests:
            is_complete = self.quest_system.check_completion(
                quest["progress"], quest["objectives"]
            )
            if is_complete:
                completable_quests.append(quest)

        if not completable_quests:
            self.quest_select.add_option(
                label="No quests are ready to turn in.", value="disabled", emoji=E.ERROR
            )
            self.quest_select.disabled = True
        else:
            for quest in completable_quests:
                self.quest_select.add_option(
                    label=f"Complete: {quest['title']}",
                    value=str(quest["id"]),
                    emoji=E.MEDAL,
                )

        self.quest_select.callback = self.complete_quest_callback
        self.add_item(self.quest_select)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.interaction_user.id:
            await interaction.response.send_message(
                "This is not your adventure.", ephemeral=True
            )
            return False
        return True

    def set_back_button(self, callback_function, label="Back"):
        """
        Allows the Guild Hall to change the back button to point
        back to the Guild Hall instead of the Profile.
        """
        self.back_button.label = label
        self.back_button.callback = callback_function

    # --- THIS FUNCTION IS MODIFIED ---
    async def complete_quest_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        quest_id = int(self.quest_select.values[0])
        
        # --- ASYNC FIX ---
        success, message = await asyncio.to_thread(
            self.quest_system.complete_quest, self.interaction_user.id, quest_id
        )
        # --- END FIX ---

        # --- THIS IS THE FIX ---
        # We no longer send an ephemeral followup.
        # We will set the embed description to the message.
        if not success:
            # If it failed, send the error message as an ephemeral followup
            await interaction.followup.send(message, ephemeral=True)
            return
        
        # On success, 'message' contains the reward text.
        # We will use this as the new embed description.
        # --- END OF FIX ---

        # --- Refresh the View In-Place ---
        new_active_quests = await asyncio.to_thread(
            self.quest_system.get_player_quests, self.interaction_user.id
        )
        
        embed = interaction.message.embeds[0]
        
        # --- THIS IS THE FIX ---
        # Set the embed description to the success message
        embed.description = message
        embed.clear_fields()
        # --- END OF FIX ---

        if not new_active_quests:
            embed.add_field(
                name="No Active Quests", value="Visit the Quest Board to accept a task."
            )
        else:
            for quest in new_active_quests:
                progress_text = []
                objectives = quest.get("objectives", {})
                progress = quest.get("progress", {})
                
                # --- THIS IS THE FIX ---
                for obj_type, tasks in objectives.items():
                    if isinstance(tasks, dict):
                        # This handles {"defeat": {"Goblin": 5}}
                        for task, required in tasks.items():
                            current = progress.get(obj_type, {}).get(task, 0)
                            progress_text.append(f"• {task}: {current} / {required}")
                    else:
                        # This handles {"locate": "Lina"}
                        task = tasks  # task is "Lina"
                        required = 1  # required is 1
                        current = progress.get(obj_type, {}).get(task, 0)
                        # --- THIS IS THE LINE TO FIX ---
                        progress_text.append(f"• {obj_type.title()} {task.title()}: {current} / {required}")
                        # --- END OF LINE TO FIX ---
                # --- END OF FIX ---
                        
                embed.add_field(
                    name=f"{quest['title']} (ID: {quest['id']})",
                    value="\n".join(progress_text) or "No objectives.",
                    inline=False,
                )

        new_view = QuestLogView(self.db, new_active_quests, self.interaction_user)
        new_view.set_back_button(self.back_button.callback, self.back_button.label)

        await interaction.edit_original_response(embed=embed, view=new_view)
    # --- END OF MODIFICATION ---


# ======================================================================
# QUEST BOARD VIEWS
# ======================================================================


class QuestBoardView(View):
    """
    Displays the list of available quests using a dropdown.
    """

    def __init__(
        self, db_manager: DatabaseManager, quests: list, interaction_user: discord.User
    ):
        super().__init__(timeout=None)
        self.db = db_manager
        self.quests = quests
        self.interaction_user = interaction_user
        self.quest_system = QuestSystem(self.db) # Create instance

        self.quest_select = Select(
            placeholder="Select a quest contract...", min_values=1, max_values=1
        )
        if not self.quests:
            self.quest_select.add_option(
                label="No quests available", value="disabled", emoji=E.ERROR
            )
            self.quest_select.disabled = True
        else:
            for quest in self.quests[:25]:
                self.quest_select.add_option(
                    label=f"[{quest['tier']}-Rank] {quest['title']}",
                    description=quest["summary"][:100],
                    value=str(quest["id"]),
                    emoji=E.HERB,
                )
        self.quest_select.callback = self.view_quest_details_callback
        self.add_item(self.quest_select)

        back_button = Button(
            label="Back to Guild Hall",
            style=discord.ButtonStyle.secondary,
            custom_id="back_to_guild_hall",
        )
        back_button.callback = back_to_guild_hall_callback
        self.add_item(back_button)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.interaction_user.id:
            await interaction.response.send_message(
                "This is not your adventure.", ephemeral=True
            )
            return False
        return True

    async def view_quest_details_callback(self, interaction: discord.Interaction):
        await interaction.response.defer() # Defer immediately
        
        quest_id = int(self.quest_select.values[0])
        
        # --- ASYNC FIX ---
        quest_details = await asyncio.to_thread(
            self.quest_system.get_quest_details, quest_id
        )
        # --- END FIX ---
        
        if not quest_details:
            await interaction.followup.send(
                f"{E.ERROR} Could not find quest details.", ephemeral=True
            )
            return

        embed = discord.Embed(
            title=f"{E.HERB} Quest: {quest_details['title']}",
            description=quest_details["description"],
            color=discord.Color.dark_teal(),
        )
        objectives_text = ""
        if "objectives" in quest_details and quest_details["objectives"]:
            for obj_type, tasks in quest_details["objectives"].items():
                if isinstance(tasks, dict):
                    for task, value in tasks.items():
                        objectives_text += (
                            f"• **{obj_type.title()}:** {task} ({value})\n"
                        )
        objectives_text = objectives_text or "No objectives listed."
        embed.add_field(name="Objectives", value=objectives_text, inline=False)

        rewards_text = ""
        if "rewards" in quest_details and quest_details["rewards"]:
            for reward, value in quest_details["rewards"].items():
                display_reward = "Aurum" if reward == "aurum" else reward.title()
                rewards_text += f"• **{display_reward}:** {value}\n"
        rewards_text = rewards_text or "No rewards listed."
        embed.add_field(name="Rewards", value=rewards_text, inline=False)
        embed.set_footer(text=f"Quest ID: {quest_id} | Tier: {quest_details['tier']}")

        view = QuestDetailView(
            self.db, quest_id, self.quests, self.interaction_user
        )
        await interaction.edit_original_response(embed=embed, view=view)


class QuestDetailView(View):
    """
    Displays the details of a single quest and allows the player to accept it.
    """

    def __init__(
        self,
        db_manager: DatabaseManager,
        quest_id: int,
        quests_list: list,
        interaction_user: discord.User,
    ):
        super().__init__(timeout=None)
        self.db = db_manager
        self.quest_id = quest_id
        self.quests_list = quests_list
        self.interaction_user = interaction_user
        self.quest_system = QuestSystem(self.db) # Create instance

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
            await interaction.response.send_message(
                "This is not your adventure.", ephemeral=True
            )
            return False
        return True

    async def accept_quest_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        # --- ASYNC FIX ---
        success = await asyncio.to_thread(
            self.quest_system.accept_quest, self.interaction_user.id, self.quest_id
        )
        # --- END FIX ---

        if success:
            await interaction.followup.send(
                f"{E.CHECK} Quest accepted! Added to your log.", ephemeral=True
            )
            # --- Go back to the quest board ---
            await self.back_to_quest_board_callback(interaction, deferred=True)
        else:
            await interaction.followup.send(
                f"{E.WARNING} You have already accepted this quest.", ephemeral=True
            )

    async def back_to_quest_board_callback(self, interaction: discord.Interaction, deferred: bool = False):
        """
        Returns to the quest board view.
        """
        if not deferred and not interaction.response.is_done():
            await interaction.response.defer()

        # --- ASYNC FIX ---
        available_quests = await asyncio.to_thread(
            self.quest_system.get_available_quests, self.interaction_user.id
        )
        # --- END FIX ---

        embed = discord.Embed(
            title=f"{E.SCROLL} Quest Board",
            description="The board is cluttered with parchment sheets...",
            color=discord.Color.dark_green(),
        )
        embed.add_field(
            name="Available Contracts",
            value="Select an available quest from the dropdown menu.",
        )
        view = QuestBoardView(self.db, available_quests, self.interaction_user)
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