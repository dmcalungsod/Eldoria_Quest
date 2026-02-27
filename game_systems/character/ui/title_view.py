"""
game_systems/character/ui/title_view.py

UI for equipping titles.
"""

import discord
from discord.ui import Button, Select, View

import cogs.utils.ui_helpers as ui_helpers
from database.database_manager import DatabaseManager


class TitleSelectView(View):
    def __init__(self, db: DatabaseManager, interaction_user: discord.User, player_data: dict):
        super().__init__(timeout=180)
        self.db = db
        self.interaction_user = interaction_user
        self.player_data = player_data
        self.titles = player_data.get("titles", [])
        self.active_title = player_data.get("active_title")

        self.add_item(self.build_title_select())

        self.back_button = Button(label="Back to Profile", style=discord.ButtonStyle.secondary, row=1)
        self.back_button.callback = ui_helpers.back_to_profile_callback
        self.add_item(self.back_button)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.interaction_user.id:
            await interaction.response.send_message("This menu is not yours.", ephemeral=True)
            return False
        return True

    def build_title_select(self) -> Select:
        select = Select(placeholder="Select a Title to Equip...", min_values=1, max_values=1, row=0)

        if not self.titles:
            select.add_option(label="No titles earned yet.", value="none", default=True)
            select.disabled = True
            return select

        # "None" option to unequip
        select.add_option(
            label="No Title",
            value="unequip",
            description="Clear your active title",
            default=(self.active_title is None),
        )

        # List titles (limit 24 + 1 none = 25 max options)
        # TODO: Implement pagination if players can earn > 24 titles
        sorted_titles = sorted(self.titles)
        for title in sorted_titles[:24]:
            is_active = title == self.active_title
            select.add_option(label=title, value=title, default=is_active, emoji="🎖️" if is_active else "🔸")

        select.callback = self.title_select_callback
        return select

    async def title_select_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        selected = interaction.data["values"][0]

        if selected == "unequip":
            self.db.set_active_title(self.interaction_user.id, None)
            msg = "Title unequipped."
        elif selected == "none":
            return
        else:
            if self.db.set_active_title(self.interaction_user.id, selected):
                msg = f"Title set to **{selected}**."
            else:
                msg = "Failed to set title (ownership check failed)."

        # Refresh
        new_p_data = self.db.get_player(self.interaction_user.id)
        embed = discord.Embed(
            title="🎖️ Title Manager",
            description=f"{msg}\n\nSelect a title from the dropdown below to display on your profile.",
            color=discord.Color.gold(),
        )

        view = TitleSelectView(self.db, self.interaction_user, new_p_data)
        await interaction.edit_original_response(embed=embed, view=view)
