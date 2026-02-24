"""
cogs/onboarding_cog.py

Character creation flow and New Player Onboarding.
Hardened against race conditions.
Atmosphere: Dark Fantasy Narrative Restored.
"""

import asyncio
import logging

import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import Button, View

import game_systems.data.emojis as E
from database.database_manager import DatabaseManager
from game_systems.data.class_data import CLASSES as CLASS_DEFINITIONS
from game_systems.data.messages import WELCOME_MESSAGE, WELCOME_TITLE
from game_systems.items.equipment_manager import EquipmentManager
from game_systems.player.player_creator import PlayerCreator

from .utils.ui_helpers import back_to_profile_callback

logger = logging.getLogger("eldoria.onboarding")


async def transition_to_guild_lobby(interaction: discord.Interaction, db: DatabaseManager, user: discord.User):
    """Helper to transition to the Guild Lobby, avoiding circular imports."""
    from game_systems.guild_system.ui.lobby_view import GuildLobbyView

    card = await asyncio.to_thread(db.get_guild_card_data, user.id)
    if not card:
        await interaction.followup.send("You are not a guild member.", ephemeral=True)
        return

    embed = discord.Embed(
        title="🏰 Adventurer’s Guild Hall",
        description=(
            f"*The receptionist nods as you approach.*\n\n"
            f"**{card['name']} — Rank {card['rank']}**\n"
            "*“How may the Guild assist you today, Adventurer?”*"
        ),
        color=discord.Color.dark_gold(),
    )

    embed.add_field(
        name="📜 Quest Board",
        value="Review available contracts and report successes.",
        inline=False,
    )
    embed.add_field(
        name="⚙️ Guild Services",
        value="Access the Shop, Exchange, Infirmary, or Training Grounds.",
        inline=False,
    )

    view = GuildLobbyView(db, user, rank=card["rank"])
    if not interaction.response.is_done():
        await interaction.response.edit_message(embed=embed, view=view)
    else:
        await interaction.edit_original_response(embed=embed, view=view)


class StartMenuView(View):
    def __init__(self, db_manager: DatabaseManager, interaction_user: discord.User):
        super().__init__(timeout=300)
        self.db = db_manager
        self.interaction_user = interaction_user
        self._init_buttons()

    def _init_buttons(self):
        sorted_classes = sorted(CLASS_DEFINITIONS.items(), key=lambda x: x[1]["id"])
        for name, data in sorted_classes:
            btn = Button(label=name, custom_id=f"cls_{data['id']}")
            btn.callback = self.class_select_callback
            self.add_item(btn)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.interaction_user.id

    async def class_select_callback(self, interaction: discord.Interaction):
        class_id = int(interaction.data["custom_id"].split("_")[1])

        class_info = next((v for k, v in CLASS_DEFINITIONS.items() if v["id"] == class_id), None)
        class_name = next((k for k, v in CLASS_DEFINITIONS.items() if v["id"] == class_id), "Unknown")

        if not class_info:
            await interaction.response.send_message("Class data error.", ephemeral=True)
            return

        # Format Stats with descriptions
        stats_str = "\n".join([f"`{k}: {v}`" for k, v in class_info["stats"].items()])

        embed = discord.Embed(
            title=f"Class: {class_name}",
            description=f"{class_info['description']}\n\n**Base Attributes**\n{stats_str}",
            color=0x00B0F4,
        )
        embed.set_footer(text="Choose wisely. This decision shapes your fate.")

        view = ClassDetailView(self.db, class_id, self.interaction_user)
        await interaction.response.edit_message(embed=embed, view=view)


class ClassDetailView(View):
    def __init__(self, db, class_id, user):
        super().__init__(timeout=300)
        self.db = db
        self.class_id = class_id
        self.user = user
        self.creator = PlayerCreator(db)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.user.id

    @discord.ui.button(label="Accept Destiny", style=discord.ButtonStyle.success)
    async def create_btn(self, interaction: discord.Interaction, button: Button):
        await interaction.response.defer()

        exists = await asyncio.to_thread(self.db.player_exists, self.user.id)
        if exists:
            await interaction.followup.send("You already have a character!", ephemeral=True)
            return

        success, msg = await asyncio.to_thread(
            self.creator.create_player,
            self.user.id,
            self.user.display_name,
            self.class_id,
        )

        if success:
            # --- RESTORED ATMOSPHERIC TEXT ---
            welcome_title = f"Welcome, {self.user.display_name}, to Astraeon City."
            welcome_desc = (
                "Your name is known, but your deeds are not. The path ahead is fraught with peril...\n\n"
                "To seek purpose, coin, or redemption, you must register with the **Adventurer's Guild**."
                "\n\n*The city gates loom above you, iron-bound and weathered by centuries of defense against the dark.*"
            )

            embed = discord.Embed(
                title=welcome_title,
                description=welcome_desc,
                color=discord.Color.dark_gold(),
            )
            embed.set_footer(text="Your journey begins now. Tread boldly.")

            view = CharacterMenuView(self.db, self.user)
            await interaction.edit_original_response(embed=embed, view=view)
        else:
            await interaction.followup.send(f"{E.WARNING} {msg}", ephemeral=True)

    @discord.ui.button(label="Reconsider", style=discord.ButtonStyle.secondary)
    async def back_btn(self, interaction: discord.Interaction, button: Button):
        embed = discord.Embed(title=WELCOME_TITLE, description=WELCOME_MESSAGE, color=discord.Color.gold())
        view = StartMenuView(self.db, self.user)
        await interaction.response.edit_message(embed=embed, view=view)


class CharacterMenuView(View):
    def __init__(self, db, user):
        super().__init__(timeout=300)
        self.db = db
        self.user = user

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.user.id

    @discord.ui.button(label="Approach Guild Clerk", style=discord.ButtonStyle.success)
    async def approach_clerk(self, interaction: discord.Interaction, button: Button):
        await interaction.response.defer()

        embed = discord.Embed(
            title="The Adventurer's Guild: Reception",
            description=(
                "The Guild Clerk looks up from a stack of parchment, adjusting her spectacles.\n\n"
                '*"Name? Class? Ah, yes. Fresh blood. Welcome to the Guild, Initiate."*\n\n'
                "She stamps a document and slides a heavy iron badge across the counter.\n\n"
                '*"We handle the paperwork; you handle the monsters. Simple, yes? '
                "But before I let you loose in the dungeon, let's see if you know which end of the weapon to hold.\"*"
            ),
            color=discord.Color.dark_teal(),
        )
        embed.set_footer(text="Complete the combat training to receive a starter kit.")

        view = GuildWelcomeView(self.db, self.user)
        await interaction.edit_original_response(embed=embed, view=view)


class GuildWelcomeView(View):
    def __init__(self, db, user):
        super().__init__(timeout=300)
        self.db = db
        self.user = user

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.user.id

    @discord.ui.button(label="⚔️ Prove Yourself (Tutorial)", style=discord.ButtonStyle.primary)
    async def start_training(self, interaction: discord.Interaction, button: Button):
        await interaction.response.defer()

        view = CombatTutorialView(self.db, self.user)
        embed = discord.Embed(
            title="⚔️ Combat Training: The Straw Knight",
            description=(
                "You step into the training ring. The sawdust floor crunches beneath your boots.\n\n"
                "A **Straw Dummy** stands before you. It mocks you with its silence and drawn-on angry eyebrows.\n\n"
                "**Action:** Strike the dummy to begin."
            ),
            color=discord.Color.red(),
        )
        await interaction.edit_original_response(embed=embed, view=view)

    @discord.ui.button(label="⏩ I know what I'm doing (Skip)", style=discord.ButtonStyle.secondary)
    async def skip_to_lobby(self, interaction: discord.Interaction, button: Button):
        await interaction.response.defer()
        await transition_to_guild_lobby(interaction, self.db, self.user)


class CombatTutorialView(View):
    def __init__(self, db, user, step=0):
        super().__init__(timeout=300)
        self.db = db
        self.user = user
        self.step = step
        self._update_buttons()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.user.id

    def _update_buttons(self):
        self.clear_items()

        if self.step == 0:
            btn = Button(
                label="⚔️ Attack",
                style=discord.ButtonStyle.danger,
                custom_id="tut_attack",
            )
            btn.callback = self.attack_callback
            self.add_item(btn)
        elif self.step == 1:
            btn = Button(
                label="🛡️ Defend",
                style=discord.ButtonStyle.primary,
                custom_id="tut_defend",
            )
            btn.callback = self.defend_callback
            self.add_item(btn)
        elif self.step == 2:
            btn = Button(
                label="⚔️ Finish It",
                style=discord.ButtonStyle.danger,
                custom_id="tut_finish",
            )
            btn.callback = self.finish_callback
            self.add_item(btn)
        elif self.step == 3:
            btn = Button(
                label="🏆 Claim Badge & Enter Guild",
                style=discord.ButtonStyle.success,
                custom_id="tut_complete",
            )
            btn.callback = self.complete_callback
            self.add_item(btn)

    async def attack_callback(self, interaction: discord.Interaction):
        self.step = 1
        self._update_buttons()

        embed = interaction.message.embeds[0]
        embed.description = (
            "**You strike the dummy!** Straw flies everywhere.\n"
            f"{E.PLAYER_ATTACK} **-5 HP**\n\n"
            "The dummy wobbles menacingly. It looks like it's winding up for a counter-wobble!\n\n"
            "**Action:** Prepare your defense!"
        )
        await interaction.response.edit_message(embed=embed, view=self)

    async def defend_callback(self, interaction: discord.Interaction):
        self.step = 2
        self._update_buttons()

        embed = interaction.message.embeds[0]
        embed.description = (
            "**You raise your guard.**\n"
            f"{E.SHIELD} **Block Success!**\n\n"
            "The dummy tips over and bonks harmlessly against your defense. **0 Damage.**\n"
            "Now, while it's off balance—finish it!"
        )
        await interaction.response.edit_message(embed=embed, view=self)

    async def finish_callback(self, interaction: discord.Interaction):
        self.step = 3
        self._update_buttons()

        embed = interaction.message.embeds[0]
        embed.title = "🏆 Training Complete!"
        embed.description = (
            "**CRITICAL HIT!**\n"
            "With a mighty blow, the straw dummy explodes into a cloud of hay.\n\n"
            'The Clerk nods slowly. *"Not bad. You didn\'t trip, at least."*\n\n'
            "You are ready for the real thing."
        )
        embed.color = discord.Color.gold()
        await interaction.response.edit_message(embed=embed, view=self)

    async def complete_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()

        # Grant a small reward - Minor Potions
        try:
            await asyncio.to_thread(
                self.db.add_inventory_item,
                self.user.id,
                "potion_minor",
                "Minor Health Potion",
                "consumable",
                "Common",
                3,
            )
        except Exception as e:
            logger.error(f"Failed to grant tutorial reward: {e}")

        # --- GRANT STARTER WEAPON ---
        player = await asyncio.to_thread(self.db.get_player, self.user.id)
        class_id = player.get("class_id") if player else None
        weapon_msg = ""

        # Class ID -> (Item Key, Item Name, Slot)
        mapping = {
            1: ("gen_sword_001", "Rusted Shortsword", "sword"),
            2: ("gen_wand_001", "Apprentice Wand", "wand"),
            3: ("gen_dagger_001", "Iron Shiv", "dagger"),
            4: ("gen_mace_001", "Acolyte's Mace", "mace"),
            5: ("gen_bow_001", "Hunter's Bow", "bow"),
        }

        if class_id in mapping:
            key, name, slot = mapping[class_id]

            # Add to Inventory
            await asyncio.to_thread(
                self.db.add_inventory_item,
                self.user.id,
                key,
                name,
                "equipment",
                "Common",
                1,
                slot,
                "equipment",  # source table
            )

            # Find the item to equip (unequipped)
            item = await asyncio.to_thread(
                self.db.find_stackable_item,
                self.user.id,
                key,
                "Common",
                slot,
                "equipment",
                equipped=0,
            )

            if item:
                # Auto-Equip
                equip_mgr = EquipmentManager(self.db)
                ok, msg = await asyncio.to_thread(equip_mgr.equip_item, self.user.id, item["id"])
                if ok:
                    weapon_msg = f"\n⚔️ **Bonus:** Received and equipped **{name}**!"
                else:
                    weapon_msg = f"\n⚔️ **Bonus:** Received **{name}**! (Check Inventory)"

        await interaction.followup.send(
            f"🎁 **Tutorial Rewards:**\n• 3x Minor Health Potion{weapon_msg}",
            ephemeral=True,
        )

        await transition_to_guild_lobby(interaction, self.db, self.user)


class OnboardingCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = DatabaseManager()

    @app_commands.command(name="start", description="Begin your adventure.")
    async def start(self, interaction: discord.Interaction):
        exists = await asyncio.to_thread(self.db.player_exists, interaction.user.id)

        if exists:
            await interaction.response.defer()
            await back_to_profile_callback(interaction, is_new_message=True)
        else:
            embed = discord.Embed(
                title=WELCOME_TITLE,
                description=WELCOME_MESSAGE,
                color=discord.Color.gold(),
            )
            view = StartMenuView(self.db, interaction.user)
            await interaction.response.send_message(embed=embed, view=view)


async def setup(bot: commands.Bot):
    await bot.add_cog(OnboardingCog(bot))
