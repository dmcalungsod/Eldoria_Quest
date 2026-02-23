import logging
from discord.ext import commands, tasks
from database.database_manager import DatabaseManager
from game_systems.adventure.adventure_resolution import AdventureResolutionEngine
from game_systems.world_time import WorldTime

logger = logging.getLogger("eldoria.loop")

class AdventureLoop(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = DatabaseManager()
        self.engine = AdventureResolutionEngine(self.bot, self.db)
        self.adventure_worker.start()

    def cog_unload(self):
        self.adventure_worker.cancel()

    @tasks.loop(minutes=1)
    async def adventure_worker(self):
        try:
            await self.bot.loop.run_in_executor(None, self._sync_worker_step)
        except Exception as e:
            logger.error(f"[AdventureLoop] Worker error: {e}", exc_info=True)

    def _sync_worker_step(self):
        now_iso = WorldTime.now().isoformat()
        due_sessions = self.db.get_adventures_ending_before(now_iso)

        if not due_sessions:
            return

        logger.info(f"[AdventureLoop] Found {len(due_sessions)} adventures to resolve.")

        for session in due_sessions:
            try:
                self.engine.resolve_session(session)
            except Exception as e:
                logger.error(f"[AdventureLoop] Failed to resolve session {session.get('discord_id')}: {e}", exc_info=True)

    @adventure_worker.before_loop
    async def before_worker(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(AdventureLoop(bot))
