"""
game_systems/help_system/handbook_view.py

Interactive view for the Guild Handbook (/help).
"""

import discord
from discord.ui import Select, View

from .handbook_content import HANDBOOK_CONTENT


class HandbookView(View):
    def __init__(self, user: discord.User):
        super().__init__(timeout=180)
        self.user = user
        self.current_section = "overview"

        # Create Select Menu
        options = []
        for key, data in HANDBOOK_CONTENT.items():
            # Clean title for label (remove emoji and strip)
            raw_title = data["title"]
            if ":" in raw_title:
                label = raw_title.split(":")[0].strip()
                desc = raw_title.split(":")[1].strip()
            else:
                label = raw_title
                desc = ""

            # Remove emoji from label if present
            if data["emoji"] in label:
                label = label.replace(data["emoji"], "").strip()

            options.append(
                discord.SelectOption(
                    label=label,
                    description=desc,
                    value=key,
                    emoji=data.get("emoji", "📜"),
                    default=(key == self.current_section),
                )
            )

        self.select_menu = Select(
            placeholder="Select a Chapter...",
            min_values=1,
            max_values=1,
            options=options,
        )
        self.select_menu.callback = self.select_callback
        self.add_item(self.select_menu)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user.id:
            await interaction.response.send_message(
                "This handbook belongs to another.", ephemeral=True
            )
            return False
        return True

    async def select_callback(self, interaction: discord.Interaction):
        selected_key = self.select_menu.values[0]
        self.current_section = selected_key

        # Update default selection visually
        for option in self.select_menu.options:
            option.default = option.value == selected_key

        content = HANDBOOK_CONTENT.get(selected_key)
        if not content:
            await interaction.response.send_message("Page torn out.", ephemeral=True)
            return

        embed = discord.Embed(
            title=content["title"],
            description=content["description"],
            color=discord.Color.dark_gold(),
        )
        # Calculate page number dynamically
        keys = list(HANDBOOK_CONTENT.keys())
        page_num = keys.index(selected_key) + 1
        embed.set_footer(text=f"Guild Handbook • Page {page_num}")

        await interaction.response.edit_message(embed=embed, view=self)
