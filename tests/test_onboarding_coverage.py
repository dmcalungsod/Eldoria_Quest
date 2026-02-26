import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from cogs.onboarding_cog import (
    CharacterMenuView,
    ClassDetailView,
    CombatTutorialView,
    OnboardingCog,
    StartMenuView,
    transition_to_guild_lobby,
)


class TestOnboardingCoverage(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.bot = MagicMock()
        self.mock_db = MagicMock()
        self.mock_interaction = MagicMock()
        self.mock_interaction.response.defer = AsyncMock()
        self.mock_interaction.followup.send = AsyncMock()
        self.mock_interaction.response.send_message = AsyncMock()
        self.mock_interaction.response.edit_message = AsyncMock()
        self.mock_interaction.edit_original_response = AsyncMock()
        self.mock_interaction.response.is_done = MagicMock(return_value=False)
        self.mock_interaction.user.id = 12345
        self.mock_interaction.user.display_name = "TestUser"

        # Patch DatabaseManager instantiation in Cog
        self.patcher_db = patch('cogs.onboarding_cog.DatabaseManager', return_value=self.mock_db)
        self.patcher_db.start()

    async def asyncTearDown(self):
        self.patcher_db.stop()

    async def test_start_command_new_player(self):
        cog = OnboardingCog(self.bot)
        self.mock_db.player_exists.return_value = False

        # We need to ensure StartMenuView can initialize (uses CLASS_DEFINITIONS)
        with patch('cogs.onboarding_cog.CLASS_DEFINITIONS', {"Warrior": {"id": 1}}):
            await cog.start.callback(cog, self.mock_interaction)

        self.mock_interaction.response.send_message.assert_called_once()
        args = self.mock_interaction.response.send_message.call_args
        self.assertIn("Sundering", args.kwargs['embed'].description)
        self.assertIsInstance(args.kwargs['view'], StartMenuView)

    async def test_start_command_existing_player(self):
        cog = OnboardingCog(self.bot)
        self.mock_db.player_exists.return_value = True

        # Mock back_to_profile_callback
        with patch('cogs.onboarding_cog.back_to_profile_callback', new_callable=AsyncMock) as mock_back:
            await cog.start.callback(cog, self.mock_interaction)
            mock_back.assert_called_once()

    async def test_start_menu_callback(self):
        # Patch CLASS_DEFINITIONS for init and callback
        with patch('cogs.onboarding_cog.CLASS_DEFINITIONS', {"Warrior": {"id": 1, "stats": {"STR": 10}, "description": "Desc"}}):
            view = StartMenuView(self.mock_db, self.mock_interaction.user)
            self.mock_interaction.data = {"custom_id": "cls_1"}

            await view.class_select_callback(self.mock_interaction)

        self.mock_interaction.response.edit_message.assert_called_once()
        args = self.mock_interaction.response.edit_message.call_args
        self.assertIn("Warrior", args.kwargs['embed'].title)
        self.assertIsInstance(args.kwargs['view'], ClassDetailView)

    async def test_class_detail_create(self):
        view = ClassDetailView(self.mock_db, 1, self.mock_interaction.user)
        view.creator.create_player = MagicMock(return_value=(True, "Created"))
        self.mock_db.player_exists.return_value = False

        # Call the extracted callback directly
        await view._create_btn_callback(self.mock_interaction, MagicMock())

        self.mock_interaction.edit_original_response.assert_called_once()
        self.assertIsInstance(self.mock_interaction.edit_original_response.call_args.kwargs['view'], CharacterMenuView)

    async def test_transition_to_guild_lobby(self):
        self.mock_db.get_guild_card_data.return_value = {"name": "User", "rank": "F"}

        # Mock GuildLobbyView import
        with patch('game_systems.guild_system.ui.lobby_view.GuildLobbyView') as MockView:
            await transition_to_guild_lobby(self.mock_interaction, self.mock_db, self.mock_interaction.user)

            # Since is_done return False
            self.mock_interaction.response.edit_message.assert_called_once()

    async def test_combat_tutorial_flow(self):
        view = CombatTutorialView(self.mock_db, self.mock_interaction.user, step=0)

        # Mock message.embeds for callback updates
        msg = MagicMock()
        msg.embeds = [MagicMock()]
        self.mock_interaction.message = msg

        await view.attack_callback(self.mock_interaction)
        self.assertEqual(view.step, 1)

        await view.defend_callback(self.mock_interaction)
        self.assertEqual(view.step, 2)

        await view.finish_callback(self.mock_interaction)
        self.assertEqual(view.step, 3)

        # Complete
        self.mock_db.get_player.return_value = {"class_id": 1}
        self.mock_db.find_stackable_item.return_value = {"id": 100}

        with patch('cogs.onboarding_cog.EquipmentManager') as MockEM:
            MockEM.return_value.equip_item.return_value = (True, "Equipped")

            # Need to patch transition_to_guild_lobby inside complete_callback
            with patch('cogs.onboarding_cog.transition_to_guild_lobby', new_callable=AsyncMock) as mock_trans:
                await view.complete_callback(self.mock_interaction)
                mock_trans.assert_called_once()

        self.mock_interaction.followup.send.assert_called()
