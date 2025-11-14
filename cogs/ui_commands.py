from datetime import datetime
import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Button
from database.database_manager import DatabaseManager
from game_systems.player.player_creator import PlayerCreator
from game_systems.data.class_data import CLASSES as CLASS_DEFINITIONS
from game_systems.data.messages import WELCOME_MESSAGE, WELCOME_TITLE
from game_systems.guild_system.quest_system import QuestSystem
from game_systems.guild_system.rank_system import RankSystem
from game_systems.data.stat_descriptions import STAT_DESCRIPTIONS

class StartMenuView(View):
    """
    The main menu view for the /start command.
    """
    def __init__(self, db_manager: DatabaseManager):
        super().__init__(timeout=None)
        self.db = db_manager
        self.create_class_buttons()

    def create_class_buttons(self):
        """
        Dynamically creates buttons for each class in the database.
        """
        conn = self.db.connect()
        cur = conn.cursor()
        cur.execute("SELECT id, name FROM classes ORDER BY id")
        classes = cur.fetchall()
        conn.close()

        for cls in classes:
            button = Button(label=cls['name'], custom_id=f"class_{cls['id']}")
            button.callback = self.class_button_callback
            self.add_item(button)

    from game_systems.data.stat_descriptions import STAT_DESCRIPTIONS

# ... (rest of the imports)

# ... (StartMenuView class)

    async def class_button_callback(self, interaction: discord.Interaction):
        """
        Callback for the class buttons. Shows the class detail view.
        """
        class_id = int(interaction.data['custom_id'].split('_')[1])
        
        class_name = None
        for name, data in CLASS_DEFINITIONS.items():
            if data['id'] == class_id:
                class_name = name
                break

        if not class_name:
            await interaction.response.send_message("This class does not exist.", ephemeral=True)
            return

        class_data = CLASS_DEFINITIONS[class_name]

        # Build the single description string
        stats_line = "  ".join([f"`{stat}: {value}`" for stat, value in class_data['stats'].items()])
        
        descriptions = "\n".join([
            f"> `{stat}` – {STAT_DESCRIPTIONS.get(stat, 'No description available.')}" 
            for stat in class_data['stats']
        ])

        description_string = (
            f"{class_data['description']}\n\n"
            f"**Base Stats**\n"
            f"{stats_line}\n\n"
            f"> **Stat Descriptions:**\n"
            f"{descriptions}\n\n"
            f"**Class ID:** {class_data['id']}"
        )

        embed = discord.Embed(
            title=class_name,
            description=description_string,
            color=0x00b0f4,
            timestamp=datetime.now()
        )

        view = ClassDetailView(self.db, class_id)
        await interaction.response.edit_message(embed=embed, view=view)


class ClassDetailView(View):
    """
    The view that shows the details of a specific class.
    """
    def __init__(self, db_manager: DatabaseManager, class_id: int):
        super().__init__(timeout=None)
        self.db = db_manager
        self.class_id = class_id
        
        create_button = Button(label="Create", style=discord.ButtonStyle.success, custom_id=f"create_{self.class_id}")
        create_button.callback = self.create_button_callback
        self.add_item(create_button)

        back_button = Button(label="Back", style=discord.ButtonStyle.secondary, custom_id="back_to_main_menu")
        back_button.callback = self.back_button_callback
        self.add_item(back_button)

    async def create_button_callback(self, interaction: discord.Interaction):
        """
        Callback for the create button. Creates a new character and updates the view.
        """
        creator = PlayerCreator(self.db)
        success, message = creator.create_player(interaction.user.id, interaction.user.display_name, self.class_id)

        if success:
            welcome_title = f"Welcome, {interaction.user.display_name}, to The Eldorian Adventurer’s Consortium."
            welcome_description = (
                "Your name has been recorded in the registry. The path ahead is fraught with peril, "
                "shadows, and whispers of forgotten power. May your will be your guide and your courage be your shield.\n\n"
                "Your journey begins now. Tread boldly."
            )
            
            embed = discord.Embed(
                title=welcome_title,
                description=welcome_description,
                color=discord.Color.dark_gold()
            )
            embed.set_footer(text="Under the watchful eyes of Guildmaster Daemon Caelungarde.")

            view = CharacterMenuView(self.db)
            await interaction.response.edit_message(embed=embed, view=view)
        else:
            await interaction.response.send_message(f"⚠️ {message}", ephemeral=True)

    async def back_button_callback(self, interaction: discord.Interaction):
        """
        Callback for the back button. Returns to the main menu.
        """
        embed = discord.Embed(
            title=WELCOME_TITLE,
            description=WELCOME_MESSAGE,
            color=discord.Color.gold()
        )
        embed.set_footer(text="Once you have chosen a class, you can create your character.")

        view = StartMenuView(self.db)
        await interaction.response.edit_message(embed=embed, view=view)


class CharacterMenuView(View):
    """
    The view displayed after a character has been created, prompting for guild registration.
    """
    def __init__(self, db_manager: DatabaseManager):
        super().__init__(timeout=None)
        self.db = db_manager

        register_button = Button(label="Register with the Guild", style=discord.ButtonStyle.success, custom_id="register_guild")
        register_button.callback = self.register_button_callback
        self.add_item(register_button)

    async def register_button_callback(self, interaction: discord.Interaction):
        """
        Callback for the register button. Registers the player in the guild and shows their Guild Card.
        """
        discord_id = interaction.user.id
        join_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        try:
            conn = self.db.connect()
            cur = conn.cursor()

            # Check if already registered
            cur.execute("SELECT * FROM guild_members WHERE discord_id = ?", (discord_id,))
            if cur.fetchone():
                await interaction.response.send_message("You are already registered with the Guild.", ephemeral=True)
                conn.close()
                return

            # Register the player
            cur.execute("INSERT INTO guild_members (discord_id, join_date) VALUES (?, ?)", (discord_id, join_date))
            conn.commit()

            # Fetch player and guild data for the card
            cur.execute("""
                SELECT p.name, c.name as class_name, p.level, p.experience, gm.rank, gm.join_date
                FROM players p
                JOIN classes c ON p.class_id = c.id
                JOIN guild_members gm ON p.discord_id = gm.discord_id
                WHERE p.discord_id = ?
            """, (discord_id,))
            card_data = cur.fetchone()
            conn.close()

            if not card_data:
                await interaction.response.send_message("Error retrieving your Guild Card.", ephemeral=True)
                return

            # Create the Guild Card embed
            embed = discord.Embed(
                title="📜 Guild Card",
                description=f"This card certifies that **{card_data['name']}** is a registered member of the The Eldorian Adventurer’s Consortium.",
                color=discord.Color.dark_gold()
            )
            embed.add_field(name="Class", value=card_data['class_name'], inline=True)
            embed.add_field(name="Rank", value=card_data['rank'], inline=True)
            embed.add_field(name="Level", value=card_data['level'], inline=True)
            embed.add_field(name="Experience", value=f"{card_data['experience']} XP", inline=True)
            embed.set_footer(text=f"Joined: {card_data['join_date']}")
            
            view = GuildCardView(self.db)
            await interaction.response.edit_message(embed=embed, view=view)

        except Exception as e:
            print(f"Error during guild registration: {e}")
            await interaction.response.send_message("An error occurred during registration.", ephemeral=True)


class GuildCardView(View):
    """
    The view for the player's Guild Card, showing main actions.
    """
    def __init__(self, db_manager: DatabaseManager):
        super().__init__(timeout=None)
        self.db = db_manager
        self.rank_system = RankSystem(self.db)
        self.quest_system = QuestSystem(self.db)

        # Add buttons for main actions
        quests_button = Button(label="View Quests", style=discord.ButtonStyle.primary, custom_id="view_quests")
        quests_button.callback = self.view_quests_callback
        self.add_item(quests_button)

        check_rank_button = Button(label="Check Rank", style=discord.ButtonStyle.secondary, custom_id="check_rank")
        check_rank_button.callback = self.check_rank_callback
        self.add_item(check_rank_button)

        promote_button = Button(label="Promote", style=discord.ButtonStyle.success, custom_id="promote", disabled=True)
        promote_button.callback = self.promote_callback
        self.add_item(promote_button)

    async def view_quests_callback(self, interaction: discord.Interaction):
        """
        Displays the quest board with available quests for the player.
        """
        await interaction.response.defer()
        available_quests = self.quest_system.get_available_quests(interaction.user.id)
        
        embed = discord.Embed(
            title="📜 Quest Board",
            description="The board is cluttered with parchment sheets—some crisp and new, others curled and water-stained. The scent of pine resin clings to them.",
            color=discord.Color.dark_green()
        )

        if not available_quests:
            embed.add_field(name="No Quests Available", value="There are currently no quests available for your rank. Check back later, adventurer.")
        else:
            for quest in available_quests:
                embed.add_field(
                    name=f"[{quest['tier']}-Rank] {quest['title']} (ID: {quest['id']})",
                    value=quest['summary'],
                    inline=False
                )

        view = QuestBoardView(self.db, available_quests)
        await interaction.edit_original_response(embed=embed, view=view)

    async def check_rank_callback(self, interaction: discord.Interaction):
        """
        Checks player's promotion eligibility and shows their progress.
        """
        await interaction.response.defer(ephemeral=True)
        discord_id = interaction.user.id
        player_data = self.rank_system.get_rank_info(discord_id)

        if not player_data:
            await interaction.followup.send("Could not retrieve your guild data.", ephemeral=True)
            return

        current_rank = player_data['rank']
        next_rank_key = self.rank_system.RANKS.get(current_rank, {}).get("next_rank")

        if not next_rank_key:
            await interaction.followup.send("You have already reached the highest available rank.", ephemeral=True)
            return

        requirements = self.rank_system.RANKS[current_rank].get("requirements", {})
        next_rank_title = self.rank_system.RANKS[next_rank_key]['title']

        # Build the progress report embed
        embed = discord.Embed(
            title=f"Promotion Evaluation: Rank {current_rank} → Rank {next_rank_key}",
            description=f"Here is your progress towards the rank of **{next_rank_title}**.",
            color=discord.Color.blue()
        )

        progress_text = ""
        eligible = True
        for req, required_value in requirements.items():
            current_value = player_data.get(req, 0)
            progress_text += f"• **{req.replace('_', ' ').title()}:** {current_value} / {required_value}\n"
            if current_value < required_value:
                eligible = False
        
        embed.add_field(name="Current Progress", value=progress_text, inline=False)

        if eligible:
            embed.color = discord.Color.green()
            embed.set_footer(text="You are eligible for promotion! The Guild Master is waiting.")
            # Enable the promote button
            for item in self.children:
                if isinstance(item, Button) and item.custom_id == "promote":
                    item.disabled = False
            await interaction.edit_original_response(view=self)
        else:
            embed.set_footer(text="Continue your efforts, adventurer.")

        await interaction.followup.send(embed=embed, ephemeral=True)


    async def promote_callback(self, interaction: discord.Interaction):
        """
        Promotes the player to the next rank.
        """
        discord_id = interaction.user.id
        success, message = self.rank_system.promote_player(discord_id)

        if success:
            # Fetch updated card data
            conn = self.db.connect()
            cur = conn.cursor()
            cur.execute("""
                SELECT p.name, c.name as class_name, p.level, p.experience, gm.rank, gm.join_date
                FROM players p
                JOIN classes c ON p.class_id = c.id
                JOIN guild_members gm ON p.discord_id = gm.discord_id
                WHERE p.discord_id = ?
            """, (discord_id,))
            card_data = cur.fetchone()
            conn.close()

            # Create the updated Guild Card embed
            embed = discord.Embed(
                title="📜 Guild Card (Promoted!)",
                description=f"This card certifies that **{card_data['name']}** is a registered member of the The Eldorian Adventurer’s Consortium.",
                color=discord.Color.gold() # Changed color for promotion
            )
            embed.add_field(name="Class", value=card_data['class_name'], inline=True)
            embed.add_field(name="New Rank", value=card_data['rank'], inline=True)
            embed.add_field(name="Level", value=card_data['level'], inline=True)
            embed.add_field(name="Experience", value=f"{card_data['experience']} XP", inline=True)
            embed.set_footer(text=f"Joined: {card_data['join_date']}")

            # Disable the promote button again
            for item in self.children:
                if isinstance(item, Button) and item.custom_id == "promote":
                    item.disabled = True

            await interaction.response.edit_message(embed=embed, view=self)
            await interaction.followup.send(message, ephemeral=True)
        else:
            await interaction.response.send_message(message, ephemeral=True)


class QuestBoardView(View):
    """
    Displays the list of available quests.
    """
    def __init__(self, db_manager: DatabaseManager, quests: list):
        super().__init__(timeout=None)
        self.db = db_manager
        self.quests = quests

        for quest in self.quests:
            button = Button(label=f"View ID: {quest['id']}", custom_id=f"view_quest_{quest['id']}")
            button.callback = self.view_quest_details_callback
            self.add_item(button)

        back_button = Button(label="Back to Guild Card", style=discord.ButtonStyle.secondary, custom_id="back_to_guild_card")
        back_button.callback = self.back_to_guild_card_callback
        self.add_item(back_button)

    async def view_quest_details_callback(self, interaction: discord.Interaction):
        quest_id = int(interaction.data['custom_id'].split('_')[-1])
        quest_system = QuestSystem(self.db)
        quest_details = quest_system.get_quest_details(quest_id)

        if not quest_details:
            await interaction.response.send_message("Could not find details for this quest.", ephemeral=True)
            return

        embed = discord.Embed(
            title=f"🌿 Quest: {quest_details['title']}",
            description=quest_details['description'],
            color=discord.Color.dark_teal()
        )
        
        objectives_text = ""
        for obj_type, tasks in quest_details['objectives'].items():
            for task, value in tasks.items():
                objectives_text += f"• **{obj_type.title()}:** {task} ({value})\n"
        embed.add_field(name="Objectives", value=objectives_text, inline=False)

        rewards_text = ""
        for reward, value in quest_details['rewards'].items():
            rewards_text += f"• **{reward.title()}:** {value}\n"
        embed.add_field(name="Rewards", value=rewards_text, inline=False)

        embed.set_footer(text=f"Quest ID: {quest_id} | Tier: {quest_details['tier']}")

        view = QuestDetailView(self.db, quest_id)
        await interaction.response.edit_message(embed=embed, view=view)

    async def back_to_guild_card_callback(self, interaction: discord.Interaction):
        """
        Returns to the main Guild Card view.
        """
        await interaction.response.defer()
        discord_id = interaction.user.id
        conn = self.db.connect()
        cur = conn.cursor()
        cur.execute("""
            SELECT p.name, c.name as class_name, p.level, p.experience, gm.rank, gm.join_date
            FROM players p
            JOIN classes c ON p.class_id = c.id
            JOIN guild_members gm ON p.discord_id = gm.discord_id
            WHERE p.discord_id = ?
        """, (discord_id,))
        card_data = cur.fetchone()
        conn.close()

        if not card_data:
            await interaction.edit_original_response(content="Error retrieving your Guild Card.", embed=None, view=None)
            return

        embed = discord.Embed(
            title="📜 Guild Card",
            description=f"This card certifies that **{card_data['name']}** is a registered member of the The Eldorian Adventurer’s Consortium.",
            color=discord.Color.dark_gold()
        )
        embed.add_field(name="Class", value=card_data['class_name'], inline=True)
        embed.add_field(name="Rank", value=card_data['rank'], inline=True)
        embed.add_field(name="Level", value=card_data['level'], inline=True)
        embed.add_field(name="Experience", value=f"{card_data['experience']} XP", inline=True)
        embed.set_footer(text=f"Joined: {card_data['join_date']}")
        
        view = GuildCardView(self.db)
        await interaction.edit_original_response(embed=embed, view=view)


class QuestDetailView(View):
    """
    Displays the details of a single quest and allows the player to accept it.
    """
    def __init__(self, db_manager: DatabaseManager, quest_id: int):
        super().__init__(timeout=None)
        self.db = db_manager
        self.quest_id = quest_id

        accept_button = Button(label="Accept Quest", style=discord.ButtonStyle.success, custom_id=f"accept_quest_{quest_id}")
        accept_button.callback = self.accept_quest_callback
        self.add_item(accept_button)

        back_button = Button(label="Back to Quest Board", style=discord.ButtonStyle.secondary, custom_id="back_to_quest_board")
        back_button.callback = self.back_to_quest_board_callback
        self.add_item(back_button)

    async def accept_quest_callback(self, interaction: discord.Interaction):
        quest_system = QuestSystem(self.db)
        success = quest_system.accept_quest(interaction.user.id, self.quest_id)

        if success:
            await interaction.response.send_message("Quest accepted! The Guild seal burns briefly across the parchment, marking your oath.", ephemeral=True)
            # Disable the accept button after accepting
            for item in self.children:
                if isinstance(item, Button) and item.custom_id == f"accept_quest_{self.quest_id}":
                    item.disabled = True
            await interaction.edit_original_response(view=self)
        else:
            await interaction.response.send_message("You have already accepted this quest or an error occurred.", ephemeral=True)

    async def back_to_quest_board_callback(self, interaction: discord.Interaction):
        """
        Returns to the quest board view.
        """
        await interaction.response.defer()
        quest_system = QuestSystem(self.db)
        available_quests = quest_system.get_available_quests(interaction.user.id)
        
        embed = discord.Embed(
            title="📜 Quest Board",
            description="The board is cluttered with parchment sheets—some crisp and new, others curled and water-stained. The scent of pine resin clings to them.",
            color=discord.Color.dark_green()
        )

        if not available_quests:
            embed.add_field(name="No Quests Available", value="There are currently no quests available for your rank. Check back later, adventurer.")
        else:
            for quest in available_quests:
                embed.add_field(
                    name=f"[{quest['tier']}-Rank] {quest['title']} (ID: {quest['id']})",
                    value=quest['summary'],
                    inline=False
                )

        view = QuestBoardView(self.db, available_quests)
        await interaction.edit_original_response(embed=embed, view=view)







class UICommands(commands.Cog):
    """
    A cog for UI-based commands.
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = DatabaseManager()

    @app_commands.command(name="start", description="Begin your journey in Eldoria.")
    async def start(self, interaction: discord.Interaction):
        """
        The main entry point for new players.
        """
        embed = discord.Embed(
            title=WELCOME_TITLE,
            description=WELCOME_MESSAGE,
            color=discord.Color.gold()
        )
        embed.set_footer(text="Once you have chosen a class, you can create your character.")

        view = StartMenuView(self.db)
        await interaction.response.send_message(embed=embed, view=view)


async def setup(bot: commands.Bot):
    await bot.add_cog(UICommands(bot))
