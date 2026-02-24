"""
game_systems/guild_system/ui/services_menu.py

Sub-menu for Guild services (Shop, Infirmary, Exchange).
Hardened: Async database loading for sub-views.
"""

import asyncio
import logging

import discord
from discord.ui import Button, View

import game_systems.data.emojis as E
from cogs.utils.ui_helpers import back_to_guild_hall_callback
from database.database_manager import DatabaseManager
from game_systems.data.shop_data import MYSTIC_MERCHANT_INVENTORY
from game_systems.events.world_event_system import WorldEventSystem

from .components import EmbedBuilder, GuildViewMixin, SystemCache, ViewFactory

logger = logging.getLogger("eldoria.ui.services")


class GuildServicesView(View, GuildViewMixin):
    def __init__(self, db_manager: DatabaseManager, interaction_user: discord.User):
        super().__init__(timeout=180)
        self.db = db_manager
        self.interaction_user = interaction_user

        self.add_item(
            ViewFactory.create_button(
                "Guild Exchange",
                discord.ButtonStyle.primary,
                "g_exchange",
                E.EXCHANGE,
                0,
                callback=self.exchange_callback,
            )
        )
        self.add_item(
            ViewFactory.create_button(
                "Guild Supply",
                discord.ButtonStyle.primary,
                "g_shop",
                "🪙",
                0,
                callback=self.shop_callback,
            )
        )
        self.add_item(
            ViewFactory.create_button(
                "Infirmary",
                discord.ButtonStyle.secondary,
                "g_infirmary",
                "❤️‍🩹",
                1,
                callback=self.infirmary_callback,
            )
        )
        self.add_item(
            ViewFactory.create_button(
                "Skill Trainer",
                discord.ButtonStyle.secondary,
                "g_trainer",
                "🧠",
                1,
                callback=self.trainer_callback,
            )
        )
        self.add_item(
            ViewFactory.create_button(
                "Alchemist",
                discord.ButtonStyle.secondary,
                "g_alchemist",
                "⚗️",
                1,
                callback=self.alchemist_callback,
            )
        )

        # Check for Mystic Merchant Event
        self.event_system = WorldEventSystem(self.db)
        active_event = self.event_system.get_current_event()
        if active_event and active_event.get("type") == WorldEventSystem.MYSTIC_MERCHANT:
            self.add_item(
                ViewFactory.create_button(
                    "Mystic Merchant",
                    discord.ButtonStyle.success,
                    "g_mystic",
                    "🔮",
                    1,
                    callback=self.mystic_merchant_callback,
                )
            )

        self.back_btn = ViewFactory.create_button(
            "Back to Guild Lobby",
            discord.ButtonStyle.grey,
            "back_lobby",
            row=2,
            callback=back_to_guild_hall_callback,
        )
        self.add_item(self.back_btn)

    async def exchange_callback(self, interaction: discord.Interaction, button: Button = None):
        from .exchange_view import GuildExchangeView

        await interaction.response.defer()
        exchange = SystemCache.get_guild_exchange(self.db)

        # Heavy calculation in thread
        val, mats = await asyncio.to_thread(exchange.calculate_exchange_value, self.interaction_user.id)

        embed = EmbedBuilder.guild_exchange()
        if val == 0:
            embed.add_field(name="Materials", value="None.")
        else:
            # Limit list length
            rows = [f"• {m['item_name']} x{m['count']}" for m in mats[:10]]
            if len(mats) > 10:
                rows.append("...")

            embed.add_field(name="Materials", value="\n".join(rows), inline=False)
            embed.add_field(name="Value", value=f"{val} Aurum", inline=False)

        view = GuildExchangeView(self.db, val > 0, self.interaction_user)
        view.set_back_button(self.back_to_services, "Back to Services")
        await interaction.edit_original_response(embed=embed, view=view)

    async def shop_callback(self, interaction: discord.Interaction, button: Button = None):
        from cogs.shop_cog import ShopView

        await interaction.response.defer()
        p_data = await asyncio.to_thread(self.db.get_player, self.interaction_user.id)
        if not p_data:
            return

        aurum = p_data["aurum"]

        embed = discord.Embed(
            title="Guild Supply",
            description=f"Funds: {aurum} Aurum",
            color=discord.Color.green(),
        )
        view = ShopView(self.db, self.interaction_user, aurum)
        view.set_back_button(self.back_to_services, "Back to Services")
        await interaction.edit_original_response(embed=embed, view=view)

    async def infirmary_callback(self, interaction: discord.Interaction, button: Button = None):
        from cogs.infirmary_cog import InfirmaryView
        from game_systems.player.player_stats import PlayerStats

        await interaction.response.defer()

        # Parallel fetch
        try:
            p_data, s_json = await asyncio.gather(
                asyncio.to_thread(self.db.get_player, self.interaction_user.id),
                asyncio.to_thread(self.db.get_player_stats_json, self.interaction_user.id),
            )
            stats = PlayerStats.from_dict(s_json)

            embed = InfirmaryView.build_infirmary_embed(p_data, stats)
            view = InfirmaryView(self.db, self.interaction_user, p_data, stats)
            view.set_back_button(self.back_to_services, "Back to Services")
            await interaction.edit_original_response(embed=embed, view=view)
        except Exception as e:
            logger.error(f"Infirmary open error: {e}")

    async def trainer_callback(self, interaction: discord.Interaction, button: Button = None):
        from cogs.skill_trainer_cog import SkillTrainerView

        await interaction.response.defer()
        p_data = await asyncio.to_thread(self.db.get_player, self.interaction_user.id)

        embed = SkillTrainerView.build_skill_embed(p_data)
        view = SkillTrainerView(self.db, self.interaction_user, p_data)
        view.set_back_button(self.back_to_services, "Back to Services")
        await interaction.edit_original_response(embed=embed, view=view)

    async def alchemist_callback(self, interaction: discord.Interaction, button: Button = None):
        from game_systems.crafting.ui.crafting_view import CraftingView

        await interaction.response.defer()

        # Build initial embed
        view = CraftingView(self.db, self.interaction_user)
        embed = view.build_embed()

        view.set_back_button(self.back_to_services, "Back to Services")
        await interaction.edit_original_response(embed=embed, view=view)

    async def mystic_merchant_callback(self, interaction: discord.Interaction, button: Button = None):
        from cogs.shop_cog import ShopView

        await interaction.response.defer()
        p_data = await asyncio.to_thread(self.db.get_player, self.interaction_user.id)
        if not p_data:
            return

        aurum = p_data["aurum"]

        embed = discord.Embed(
            title="🔮 Mystic Merchant",
            description=f"A cloaked figure displays wares that shimmer with strange energy.\n\nFunds: {aurum} Aurum",
            color=discord.Color.purple(),
        )
        view = ShopView(self.db, self.interaction_user, aurum, inventory=MYSTIC_MERCHANT_INVENTORY)
        view.set_back_button(self.back_to_services, "Back to Services")
        await interaction.edit_original_response(embed=embed, view=view)

    async def back_to_services(self, interaction: discord.Interaction):
        await interaction.response.defer()
        view = GuildServicesView(self.db, self.interaction_user)
        await interaction.edit_original_response(embed=EmbedBuilder.services_menu(), view=view)
