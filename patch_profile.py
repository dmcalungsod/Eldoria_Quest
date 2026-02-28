
with open("game_systems/character/ui/profile_view.py") as f:
    content = f.read()

content = content.replace('''    async def settings_callback(self, interaction: discord.Interaction):
        """Opens the Settings Menu."""
        await interaction.response.defer()

        embed = discord.Embed(
            title="⚙️ Settings",
            description="Manage your account and preferences.",
            color=discord.Color.light_grey(),
        )

        view = SettingsView(self.db, self.interaction_user)
        await interaction.edit_original_response(embed=embed, view=view)''', '''    async def settings_callback(self, interaction: discord.Interaction):
        """Opens the Settings Menu."""
        await ui_helpers.navigate_to_settings(interaction, self.db, self.interaction_user)''')

with open("game_systems/character/ui/profile_view.py", "w") as f:
    f.write(content)
