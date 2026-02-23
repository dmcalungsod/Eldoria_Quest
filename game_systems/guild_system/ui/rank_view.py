"""
game_systems/guild_system/ui/rank_view.py

Refined Rank / Promotion UI for the Adventurer's Guild.
Hardened: Async database calls, robust error handling, and logging.
"""

import asyncio
import logging

import discord
from discord.ui import View

import game_systems.data.emojis as E
from cogs.ui_helpers import back_to_guild_hall_callback
from database.database_manager import DatabaseManager

from .components import GuildViewMixin, SystemCache, ViewFactory

logger = logging.getLogger("eldoria.ui.rank")


class RankProgressView(View, GuildViewMixin):
    """
    Displays the player's current rank progress and a button to begin the Promotion Trial.
    """

    def __init__(
        self,
        db_manager: DatabaseManager,
        eligible: bool,
        interaction_user: discord.User,
    ):
        super().__init__(timeout=180)
        self.db = db_manager
        self.interaction_user = interaction_user
        self.rank_system = SystemCache.get_rank_system(db_manager)

        # Primary action: begin the promotion trial (if eligible)
        self.promote_btn = ViewFactory.create_button(
            label="Begin Promotion Trial",
            style=discord.ButtonStyle.success,
            custom_id="req_promo",
            disabled=not eligible,
            callback=self.promote_callback,
        )
        self.add_item(self.promote_btn)

        # Secondary: return to the Guild Hall
        self.back_btn = ViewFactory.create_button(
            label="Back to Guild Hall",
            style=discord.ButtonStyle.secondary,
            custom_id="back_gh",
            row=1,
            callback=back_to_guild_hall_callback,
        )
        self.add_item(self.back_btn)

    async def promote_callback(self, interaction: discord.Interaction):
        """
        Re-verify eligibility then present a confirmation screen describing the Promotion Trial.
        """
        await interaction.response.defer()

        try:
            # Re-check eligibility (threaded DB call)
            eligible = await asyncio.to_thread(
                self.rank_system.check_promotion_eligibility, self.interaction_user.id
            )
            if not eligible:
                await interaction.followup.send(
                    f"{E.WARNING} You no longer meet the promotion requirements.",
                    ephemeral=True,
                )
                return

            # Fetch current rank info to determine the target rank
            player_info = await asyncio.to_thread(
                self.rank_system.get_rank_info, self.interaction_user.id
            )
            current_rank = player_info.get("rank", "F")
            next_rank_key = self.rank_system.get_next_rank(current_rank)

            if not next_rank_key:
                await interaction.followup.send(
                    f"{E.MEDAL} You have already reached the highest rank.",
                    ephemeral=True,
                )
                return

            next_rank_title = self.rank_system.RANKS.get(next_rank_key, {}).get(
                "title", next_rank_key
            )

            # Build confirmation embed (clear, thematic, and explicit)
            embed = discord.Embed(
                title=f"{E.WARNING} Promotion Trial — Rank {next_rank_key}",
                description=(
                    f"You stand before the threshold of advancement to **{next_rank_title}**.\n\n"
                    "**Trial Conditions**\n"
                    "• This encounter is **Boss-Tier** and far more lethal than normal assignments.\n"
                    "• **Auto-Combat is disabled.** You will face the Examiner in manual, turn-based combat.\n"
                    "• Failure means you do not pass the trial — prepare accordingly.\n\n"
                    "Do you accept the challenge and step into the arena?"
                ),
                color=discord.Color.orange(),
            )

            view = RankTrialConfirmationView(
                self.db, self.interaction_user, next_rank_key
            )
            await interaction.edit_original_response(embed=embed, view=view)

        except Exception as e:
            logger.error(
                f"Promotion callback error for {self.interaction_user.id}: {e}",
                exc_info=True,
            )
            await interaction.followup.send(
                "An error occurred checking eligibility.", ephemeral=True
            )


class RankTrialConfirmationView(View, GuildViewMixin):
    """
    Confirmation screen shown immediately before starting a Promotion Trial.
    Responsible for starting the special promotion adventure session.
    """

    def __init__(
        self,
        db_manager: DatabaseManager,
        interaction_user: discord.User,
        next_rank: str,
    ):
        super().__init__(timeout=180)
        self.db = db_manager
        self.interaction_user = interaction_user
        self.next_rank = next_rank

        # Accept challenge (dangerous)
        self.accept_btn = ViewFactory.create_button(
            label="Accept Challenge",
            style=discord.ButtonStyle.danger,
            custom_id="confirm_trial",
            emoji="⚔️",
            callback=self.confirm_callback,
        )
        self.add_item(self.accept_btn)

        # Return to previous menu
        self.return_btn = ViewFactory.create_button(
            label="Return",
            style=discord.ButtonStyle.grey,
            custom_id="cancel_trial",
            callback=self.cancel_callback,
        )
        self.add_item(self.return_btn)

    async def confirm_callback(self, interaction: discord.Interaction):
        """
        Start the promotion trial special adventure session and redirect the user to the
        Exploration UI for the trial (handled by AdventureManager).
        """
        await interaction.response.defer()

        # Obtain AdventureCommands cog and its manager
        adventure_cog = interaction.client.get_cog("AdventureCommands")
        if not adventure_cog:
            await interaction.followup.send(
                f"{E.ERROR} Adventure system is currently offline.", ephemeral=True
            )
            return

        # Start the promotion trial session in a thread-safe manner
        try:
            await asyncio.to_thread(
                adventure_cog.manager.start_promotion_trial,
                self.interaction_user.id,
                self.next_rank,
            )
        except Exception as exc:
            logger.error(f"Failed to start trial for {self.interaction_user.id}: {exc}")
            await interaction.followup.send(
                f"{E.ERROR} Failed to start promotion trial.", ephemeral=True
            )
            return

        # Local imports to avoid circular dependencies and keep startup fast
        from game_systems.adventure.ui.adventure_embeds import AdventureEmbeds
        from game_systems.adventure.ui.exploration_view import ExplorationView
        from game_systems.player.player_stats import PlayerStats

        try:
            # Gather data required to build the Exploration embed/view
            stats_json = await asyncio.to_thread(
                self.db.get_player_stats_json, self.interaction_user.id
            )
            stats = PlayerStats.from_dict(stats_json)
            vitals = await asyncio.to_thread(
                self.db.get_player_vitals, self.interaction_user.id
            )
            session_row = await asyncio.to_thread(
                adventure_cog.manager.get_active_session, self.interaction_user.id
            )
            player_data = await asyncio.to_thread(
                self.db.get_player, self.interaction_user.id
            )
            class_id = player_data["class_id"] if player_data else 1

            import json

            active_monster = None
            if session_row and session_row["active_monster_json"]:
                active_monster = json.loads(session_row["active_monster_json"])

            # Compose embed describing the start of the trial
            embed = AdventureEmbeds.build_exploration_embed(
                location_id="guild_arena",
                log=[
                    "You step into the arena. The Examiner's presence hangs heavy in the air."
                ],
                player_stats=stats,
                vitals=vitals,
                active_monster=active_monster,
                class_id=class_id,
            )

            # Build the exploration view and hand control over to the Adventure system
            view = ExplorationView(
                self.db,
                adventure_cog.manager,
                location_id="guild_arena",
                log=["Trial Started."],
                interaction_user=self.interaction_user,
                player_stats=stats,
                vitals=vitals,
                active_monster=active_monster,
            )

            await interaction.edit_original_response(embed=embed, view=view)

        except Exception as e:
            logger.error(f"Trial UI load error: {e}", exc_info=True)
            await interaction.followup.send(
                "Error loading arena interface.", ephemeral=True
            )

    async def cancel_callback(self, interaction: discord.Interaction):
        """
        Reconstruct the RankProgressView and return the user to it.
        We re-fetch the relevant rank data to ensure the display is up-to-date.
        """
        await interaction.response.defer()

        # Safe local import for rank system
        from .components import SystemCache  # local import to avoid circular issues

        rank_system = SystemCache.get_rank_system(self.db)

        # Re-check eligibility and fetch player rank info
        eligible = await asyncio.to_thread(
            rank_system.check_promotion_eligibility, self.interaction_user.id
        )
        player_info = await asyncio.to_thread(
            rank_system.get_rank_info, self.interaction_user.id
        )
        current_rank = player_info.get("rank", "F")
        next_rank_key = rank_system.RANKS.get(current_rank, {}).get("next_rank")

        # Build a compact progress embed for returning
        next_rank_title = (
            rank_system.RANKS.get(next_rank_key, {}).get("title")
            if next_rank_key
            else "—"
        )
        embed = discord.Embed(
            title=f"{E.MEDAL} Promotion Evaluation: {current_rank} → {next_rank_key or 'N/A'}",
            description=f"Progress toward the title **{next_rank_title}**.",
            color=discord.Color.blue(),
        )

        # Rebuild requirement progress text
        requirements = rank_system.RANKS.get(current_rank, {}).get("requirements", {})
        progress_lines = []
        for req, required_value in requirements.items():
            current_value = player_info.get(req, 0)
            progress_lines.append(
                f"• **{req.replace('_', ' ').title()}:** {current_value} / {required_value}"
            )

        embed.add_field(
            name="Current Progress",
            value="\n".join(progress_lines) or "No tracked progress.",
            inline=False,
        )

        if eligible:
            embed.color = discord.Color.green()
            embed.set_footer(
                text="You meet the requirements. When ready, attempt the Promotion Trial."
            )

        # Rebuild RankProgressView and set its back button to point back to QuestsMenu (safe callback)
        view = RankProgressView(self.db, eligible, self.interaction_user)

        # Create a minimal back-to-quests callback inline to avoid import ordering issues
        from .components import EmbedBuilder
        from .quests_menu import QuestsMenuView

        async def back_to_quests_callback(inter: discord.Interaction):
            await inter.response.defer()
            v = QuestsMenuView(self.db, self.interaction_user)
            # Use EmbedBuilder (if available) to present the quests menu; fallback to a simple embed
            try:
                embed_menu = EmbedBuilder.quest_menu()
            except Exception:
                embed_menu = discord.Embed(
                    title="Quests",
                    description="Guild quest board.",
                    color=discord.Color.dark_green(),
                )
            await inter.edit_original_response(embed=embed_menu, view=v)

        # Attach the back callback
        view.set_back_button(back_to_quests_callback, "Back to Quests")

        await interaction.edit_original_response(embed=embed, view=view)
