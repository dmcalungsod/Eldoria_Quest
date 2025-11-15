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

from database.database_manager import DatabaseManager
from game_systems.guild_system.quest_system import QuestSystem
import game_systems.data.emojis as E

# --- Local Imports ---
from .ui_helpers import back_to_guild_card_callback

# ======================================================================
# QUEST LOG VIEW
# ======================================================================


class QuestLogView(View):
    """
    Displays the player's currently accepted quests.
    """

    def __init__(self, db_manager: DatabaseManager):
        super().__init__(timeout=None)
        self.db = db_manager

        # Button 1: Back to Guild Card
        back_button = Button(
            label="Back to Guild Card",
            style=discord.ButtonStyle.secondary,
            custom_id="back_to_guild_card",
        )
        back_button.callback = back_to_guild_card_callback
        self.add_item(back_button)

        # In the future, we can add "Complete Quest" buttons here.


# ======================================================================
# QUEST BOARD VIEWS
# ======================================================================


class QuestBoardView(View):
    """
    Displays the list of available quests using a dropdown (Select) menu.
    """

    def __init__(self, db_manager: DatabaseManager, quests: list):
        super().__init__(timeout=None)
        self.db = db_manager
        self.quests = quests

        # --- NEW: Create the Select Menu ---
        self.quest_select = Select(
            placeholder="Select a quest contract from the board...",
            min_values=1,
            max_values=1,
        )

        # Populate the dropdown with quests
        if not self.quests:
            self.quest_select.add_option(
                label="No quests available",
                description="Check back later or rank up.",
                value="disabled",
                emoji=E.ERROR,
            )
            self.quest_select.disabled = True
        else:
            # Discord Select Menus have a 25 option limit
            for quest in self.quests[:25]:
                self.quest_select.add_option(
                    label=f"[{quest['tier']}-Rank] {quest['title']}",
                    # Descriptions have a 100-char limit
                    description=quest["summary"][:100],
                    value=str(quest["id"]),  # Value must be a string
                    emoji=E.HERB,
                )

        self.quest_select.callback = self.view_quest_details_callback
        self.add_item(self.quest_select)

        # --- Add the Back Button ---
        back_button = Button(
            label="Back to Guild Card",
            style=discord.ButtonStyle.secondary,
            custom_id="back_to_guild_card",
        )
        back_button.callback = back_to_guild_card_callback  # Use the global helper
        self.add_item(back_button)

    async def view_quest_details_callback(self, interaction: discord.Interaction):
        """
        This is the callback for the *Select menu*.
        It fires when a user chooses a quest from the dropdown.
        """
        # Get the quest ID from the select menu's values
        quest_id = int(self.quest_select.values[0])

        quest_system = QuestSystem(self.db)
        quest_details = quest_system.get_quest_details(quest_id)

        if not quest_details:
            await interaction.response.send_message(
                f"{E.ERROR} Could not find details for this quest.", ephemeral=True
            )
            return

        embed = discord.Embed(
            title=f"{E.HERB} Quest: {quest_details['title']}",
            description=quest_details["description"],
            color=discord.Color.dark_teal(),
        )

        objectives_text = ""
        for obj_type, tasks in quest_details["objectives"].items():
            if isinstance(tasks, dict):
                for task, value in tasks.items():
                    objectives_text += f"• **{obj_type.title()}:** {task} ({value})\n"
            else:
                objectives_text += f"• **{obj_type.title()}:** {tasks}\n"

        embed.add_field(name="Objectives", value=objectives_text, inline=False)

        rewards_text = ""
        if "rewards" in quest_details and quest_details["rewards"]:
            for reward, value in quest_details["rewards"].items():
                # Display "Gold" from quests as "Aurum"
                display_reward = "Aurum" if reward == "gold" else reward.title()
                rewards_text += f"• **{display_reward}:** {value}\n"
        else:
            rewards_text = "No rewards listed."

        embed.add_field(name="Rewards", value=rewards_text, inline=False)
        embed.set_footer(text=f"Quest ID: {quest_id} | Tier: {quest_details['tier']}")

        view = QuestDetailView(self.db, quest_id)
        # Edit the message to show the Quest Detail screen
        await interaction.response.edit_message(embed=embed, view=view)


class QuestDetailView(View):
    """
    Displays the details of a single quest and allows the player to accept it.
    """

    def __init__(self, db_manager: DatabaseManager, quest_id: int):
        super().__init__(timeout=None)
        self.db = db_manager
        self.quest_id = quest_id

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

    async def accept_quest_callback(self, interaction: discord.Interaction):
        """
        Callback for the 'Accept Quest' button.
        On success, automatically navigates back to the quest board.
        On failure, sends an ephemeral error.
        """
        quest_system = QuestSystem(self.db)
        success = quest_system.accept_quest(interaction.user.id, self.quest_id)

        if success:
            # Automatically go back to the quest board
            await self.back_to_quest_board_callback(interaction)
        else:
            # Failure (like already having the quest) IS a branching reply.
            await interaction.response.send_message(
                f"{E.WARNING} You have already accepted this quest or an error occurred.",
                ephemeral=True,
            )

    async def back_to_quest_board_callback(self, interaction: discord.Interaction):
        """
        Returns to the quest board view.
        """
        if not interaction.response.is_done():
            await interaction.response.defer()

        db = DatabaseManager()  # Need a fresh instance for the new view
        quest_system = QuestSystem(db)
        available_quests = quest_system.get_available_quests(interaction.user.id)

        embed = discord.Embed(
            title=f"{E.SCROLL} Quest Board",
            description="The board is cluttered with parchment sheets—some crisp and new, others curled and water-stained. The scent of pine resin clings to them.",
            color=discord.Color.dark_green(),
        )

        # This embed description is now the primary way to see quests
        # The dropdown will contain the selectable list.
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

        view = QuestBoardView(db, available_quests)
        await interaction.edit_original_response(embed=embed, view=view)


# ======================================================================
# COG LOADER
# ======================================================================


class QuestHubCog(commands.Cog):
    """
    A cog for housing all Guild-related Quest Views.
    This cog has no commands, it just makes the Views loadable.
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = DatabaseManager()


async def setup(bot: commands.Bot):
    await bot.add_cog(QuestHubCog(bot))
