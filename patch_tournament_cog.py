import re

with open("cogs/tournament_cog.py") as f:
    content = f.read()

# Add import
if "from cogs.utils.announcer import announce_to_guilds" not in content:
    content = content.replace("from database.database_manager import DatabaseManager", "from database.database_manager import DatabaseManager\nfrom cogs.utils.announcer import announce_to_guilds")

# Replace _announce calls
content = re.sub(r"await self\._announce\(", "await announce_to_guilds(self.bot, ", content)

# Remove _announce method
content = re.sub(r'    async def _announce\(self, message: str\):[\s\S]*?logger\.error\(f"Failed to announce in {guild\.name}: {e}"\)\n\n', "", content)

with open("cogs/tournament_cog.py", "w") as f:
    f.write(content)
