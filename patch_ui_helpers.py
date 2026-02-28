
with open("cogs/utils/ui_helpers.py") as f:
    content = f.read()

new_logic = """
async def navigate_to_settings(interaction: discord.Interaction, db, user):
    \"\"\"Navigation: Opens the Settings Menu.\"\"\"
    from game_systems.character.ui.settings_view import SettingsView

    if not interaction.response.is_done():
        await interaction.response.defer()

    embed = discord.Embed(
        title="⚙️ Settings",
        description="Manage your account and preferences.",
        color=discord.Color.light_grey(),
    )
    view = SettingsView(db, user)
    await interaction.edit_original_response(embed=embed, view=view)
"""

if "navigate_to_settings" not in content:
    content += new_logic
    with open("cogs/utils/ui_helpers.py", "w") as f:
        f.write(content)
