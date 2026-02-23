"""
game_systems/character/ui/profile_view.py

Main Hub for the player's interface.
Hardened: Async database calls for status updates and sub-menus.
"""

import asyncio
import json
import logging

import discord
from discord.ui import Button, View

# Helper imports (careful: avoid circular dependencies)
import cogs.ui_helpers as ui_helpers
import game_systems.data.emojis as E
from cogs.status_update_cog import StatusUpdateView
from database.database_manager import DatabaseManager
from game_systems.player.player_stats import PlayerStats

# Modular imports
from .abilities_view import AbilitiesView
from .adventure_menu import AdventureView
from .settings_view import SettingsView
from game_systems.chronicle.ui.chronicle_view import ChroniclesView

logger = logging.getLogger("eldoria.ui.profile")


class CharacterTabView(View):
    """
    Main interface for an Adventurer's Character Profile.
    Provides access to abilities, expeditions, and vitals.
    """

    def __init__(self, db_manager: DatabaseManager, interaction_user: discord.User):
        super().__init__(timeout=180)
        self.db = db_manager
        self.interaction_user = interaction_user

        # --- Expedition / Adventure (Row 0, Primary) ---
        btn_adventure = Button(
            label="Expeditions",
            style=discord.ButtonStyle.success,
            custom_id="adventure",
            emoji="🗺️",
            row=0,
        )
        btn_adventure.callback = self.adventure_callback
        self.add_item(btn_adventure)

        # --- Abilities & Kit (Row 1, Primary for Character Management) ---
        btn_abilities = Button(
            label="Abilities & Kit",
            style=discord.ButtonStyle.primary,
            custom_id="abilities",
            emoji=E.BACKPACK,
            row=1,
        )
        btn_abilities.callback = self.abilities_callback
        self.add_item(btn_abilities)

        # --- Status: Vestige & Vitals (Row 1, Secondary) ---
        btn_status = Button(
            label="Vestige & Vitals",
            style=discord.ButtonStyle.secondary,
            custom_id="status",
            emoji=E.VESTIGE,
            row=1,
        )
        btn_status.callback = self.status_callback
        self.add_item(btn_status)

        # --- Guild Hall (Row 2, New Placement for Direct Access) ---
        btn_guild = Button(
            label="Guild Hall",
            style=discord.ButtonStyle.secondary,
            custom_id="gh_link",
            emoji="🏦",
            row=2,
        )
        btn_guild.callback = self.guild_hall_callback
        self.add_item(btn_guild)

        # --- Settings (Row 2) ---
        btn_settings = Button(
            label="Settings",
            style=discord.ButtonStyle.secondary,
            custom_id="settings_link",
            emoji="⚙️",
            row=2,
        )
        btn_settings.callback = self.settings_callback
        self.add_item(btn_settings)

        # --- Chronicles (Row 2) ---
        btn_chronicles = Button(
            label="Chronicles",
            style=discord.ButtonStyle.secondary,
            custom_id="chronicles_link",
            emoji="🏆",
            row=2,
        )
        btn_chronicles.callback = self.chronicles_callback
        self.add_item(btn_chronicles)

    # ------------------------------------------------------------------
    # Interaction Permissions Check
    # ------------------------------------------------------------------

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.interaction_user.id:
            await interaction.response.send_message("This profile does not belong to you.", ephemeral=True)
            return False
        return True

    # ------------------------------------------------------------------
    # Tabs
    # ------------------------------------------------------------------

    async def abilities_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        embed = discord.Embed(
            title="📜 Abilities & Kit",
            description=(
                "*Your gathered knowledge, arms, and practiced arts.*\nManage inventory, equipment, and skills."
            ),
            color=discord.Color.purple(),
        )
        view = AbilitiesView(self.db, self.interaction_user)
        await interaction.edit_original_response(embed=embed, view=view)

    async def adventure_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()

        # Check for active session
        session = await asyncio.to_thread(self.db.get_active_adventure, self.interaction_user.id)
        has_active_session = session is not None

        embed = discord.Embed(
            title="🗺️ Expeditions",
            description=(
                "*Beyond the city wards, the world grows darker.*\n"
                "Begin or resume an expedition into the wilds of Eldoria."
            ),
            color=discord.Color.dark_teal(),
        )
        view = AdventureView(self.db, self.interaction_user, active_session=has_active_session)
        await interaction.edit_original_response(embed=embed, view=view)

    async def status_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()

        try:
            # Fetch player data and stats concurrently in threads
            p_data, s_row = await asyncio.gather(
                asyncio.to_thread(self.db.get_player, self.interaction_user.id),
                asyncio.to_thread(self.db.get_player_stats_row, self.interaction_user.id),
            )

            if not p_data or not s_row:
                await interaction.followup.send("Error retrieving character data.", ephemeral=True)
                return

            stats = PlayerStats.from_dict(json.loads(s_row["stats_json"]))

            embed = StatusUpdateView.build_status_embed(p_data, stats, s_row)
            view = StatusUpdateView(self.db, self.interaction_user, p_data, stats, s_row)

            # Assign profile return callback via helper
            view.back_button.callback = ui_helpers.back_to_profile_callback

            await interaction.edit_original_response(embed=embed, view=view)
        except Exception as e:
            logger.error(
                f"Status callback error for {self.interaction_user.id}: {e}",
                exc_info=True,
            )
            await interaction.followup.send("System error loading status.", ephemeral=True)

    async def guild_hall_callback(self, interaction: discord.Interaction):
        """Opens the Guild Hall Lobby directly."""
        if not interaction.response.is_done():
            await interaction.response.defer()

        # Calls shared logic in ui_helpers to load the Guild Hall
        await ui_helpers.back_to_guild_hall_callback(interaction)

    async def settings_callback(self, interaction: discord.Interaction):
        """Opens the Settings Menu."""
        await interaction.response.defer()

        embed = discord.Embed(
            title="⚙️ Settings",
            description="Manage your account and preferences.",
            color=discord.Color.light_grey(),
        )

        view = SettingsView(self.db, self.interaction_user)
        await interaction.edit_original_response(embed=embed, view=view)

    async def chronicles_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()

        titles = await asyncio.to_thread(self.db.get_titles, self.interaction_user.id)
        active_title = await asyncio.to_thread(self.db.get_active_title, self.interaction_user.id)

        description = "*Your deeds are etched in history.*"

        embed = discord.Embed(
            title="🏆 Chronicles & Titles",
            description=description,
            color=discord.Color.gold(),
        )

        embed.add_field(
            name="Active Title",
            value=f"**{active_title}**" if active_title else "*None*",
            inline=False,
        )

        if titles:
            titles.sort()
            titles_str = ", ".join([f"`{t}`" for t in titles])
            embed.add_field(name=f"Unlocked Titles ({len(titles)})", value=titles_str, inline=False)
        else:
            embed.add_field(name="Unlocked Titles", value="*No titles earned yet.*", inline=False)

        view = ChroniclesView(self.db, self.interaction_user, titles, active_title)
        await interaction.edit_original_response(embed=embed, view=view)
