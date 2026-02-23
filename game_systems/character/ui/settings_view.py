"""
game_systems/character/ui/settings_view.py

Settings and Account Management UI.
Includes Character Reset functionality.
"""

import logging

import discord
from discord.ui import Button, View

import cogs.ui_helpers as ui_helpers
import game_systems.data.emojis as E
from database.database_manager import DatabaseManager

logger = logging.getLogger("eldoria.ui.settings")


class SettingsView(View):
    """
    General Settings Menu.
    Currently only houses the 'Reset Character' option.
    """

    def __init__(self, db_manager: DatabaseManager, interaction_user: discord.User):
        super().__init__(timeout=180)
        self.db = db_manager
        self.interaction_user = interaction_user

        # Reset Character Button
        btn_reset = Button(
            label="Reset Character",
            style=discord.ButtonStyle.danger,
            custom_id="settings_reset",
            emoji="💀",
            row=0,
        )
        btn_reset.callback = self.reset_callback
        self.add_item(btn_reset)

        # Back Button
        btn_back = Button(
            label="Back to Profile",
            style=discord.ButtonStyle.secondary,
            custom_id="settings_back",
            emoji="↩️",
            row=1,
        )
        btn_back.callback = ui_helpers.back_to_profile_callback
        self.add_item(btn_back)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.interaction_user.id:
            await interaction.response.send_message(
                "This menu does not belong to you.", ephemeral=True
            )
            return False
        return True

    async def reset_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()

        embed = discord.Embed(
            title="⚠️ DANGER ZONE: Character Reset",
            description=(
                "**Are you absolutely sure you want to delete your character?**\n\n"
                "• All Stats, Skills, and XP will be lost.\n"
                "• Inventory, Gold, and Vestige will be deleted.\n"
                "• Quest progress and Guild Rank will be erased.\n\n"
                "**This action cannot be undone.**"
            ),
            color=discord.Color.red(),
        )

        view = ResetConfirmationView(self.db, self.interaction_user)
        await interaction.edit_original_response(embed=embed, view=view)


class ResetConfirmationView(View):
    """
    Confirmation dialog for character deletion.
    """

    def __init__(self, db_manager: DatabaseManager, interaction_user: discord.User):
        super().__init__(timeout=60)
        self.db = db_manager
        self.interaction_user = interaction_user

        # Confirm Button
        btn_confirm = Button(
            label="CONFIRM WIPE",
            style=discord.ButtonStyle.danger,
            custom_id="confirm_reset",
            emoji="🗑️",
        )
        btn_confirm.callback = self.confirm_callback
        self.add_item(btn_confirm)

        # Cancel Button
        btn_cancel = Button(
            label="Cancel",
            style=discord.ButtonStyle.secondary,
            custom_id="cancel_reset",
        )
        btn_cancel.callback = self.cancel_callback
        self.add_item(btn_cancel)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.interaction_user.id:
            await interaction.response.send_message(
                "This menu does not belong to you.", ephemeral=True
            )
            return False
        return True

    async def confirm_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()

        try:
            # Execute Hard Delete
            self.db.delete_player_full(self.interaction_user.id)

            logger.warning(
                f"User {self.interaction_user.id} ({self.interaction_user.name}) reset their character."
            )

            embed = discord.Embed(
                title="Character Deleted",
                description=(
                    "Your records have been expunged from the archives.\n"
                    "The world forgets your name, and your deeds fade into silence.\n\n"
                    "To begin a new journey, use `/start`."
                ),
                color=discord.Color.dark_grey(),
            )
            # Remove all buttons/views
            await interaction.edit_original_response(embed=embed, view=None)

        except Exception as e:
            logger.error(
                f"Error resetting character for {self.interaction_user.id}: {e}"
            )
            await interaction.followup.send(
                "System error during deletion. Please contact an admin.", ephemeral=True
            )

    async def cancel_callback(self, interaction: discord.Interaction):
        # Return to Settings Menu
        await interaction.response.defer()

        embed = discord.Embed(
            title="⚙️ Settings",
            description="Manage your account and preferences.",
            color=discord.Color.light_grey(),
        )
        view = SettingsView(self.db, self.interaction_user)
        await interaction.edit_original_response(embed=embed, view=view)
