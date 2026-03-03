# Eldoria Quest - Discord Bot

## Overview
Eldoria Quest is a dark high-fantasy idle RPG Discord bot inspired by Danmachi and Grimgar of Fantasy and Ash. The bot provides an immersive, persistent adventure experience with a material-based economy, turn-by-turn combat, and guild progression.

## Recent Updates (November 15, 2025)

### Code Optimizations
- **Database Performance**: Added context manager pattern for automatic connection management with proper rollback/commit handling
- **Type Safety**: Fixed type hints throughout the codebase (Optional[str] instead of str = None)
- **Resource Management**: Implemented proper connection pooling and cleanup to prevent memory leaks
- **Error Handling**: Enhanced error handling with automatic rollback on failures

### Testing Infrastructure
- **Comprehensive Test Suite**: Added complete test coverage for:
  - Database operations (CRUD, schema, population)
  - Player systems (stats, vitals, progression)
  - Inventory and equipment management
  - Combat engine and damage calculations
  - Level-up mechanics
- **Test Files**:
  - `tests/test_database.py`: Database and data integrity tests
  - `tests/test_game_systems.py`: Game mechanics and systems tests
  - `tests/run_all_tests.py`: Master test runner

### Security Improvements
- All credentials properly sourced from environment variables
- No hardcoded secrets anywhere in codebase
- Parameterized SQL queries throughout (SQL injection protected)
- Validated table names with whitelist for dynamic queries

## Project Architecture

### Core Systems

#### Database Layer (`database/`)
- **SQLite Database**: Local file-based storage (EQ_Game.db)
- **DatabaseManager**: Centralized database operations with context managers
- **Schema**: Comprehensive tables for players, monsters, equipment, quests, guilds
- **Population Scripts**: Auto-populate game data on startup

#### Game Systems (`game_systems/`)
- **Adventure System**: Exploration mechanics with random encounters
- **Combat Engine**: Turn-based combat with auto-skill AI
- **Player Progression**: Stats, leveling, and skill systems
- **Item Management**: Equipment, consumables, and inventory
- **Guild System**: Ranks, quests, and material exchange
- **Loot System**: Material-based economy (no coin drops)

#### Discord Integration (`cogs/`)
- **Onboarding**: Character creation via `/start` command
- **Character Management**: Profile, inventory, skills UI
- **Guild Hub**: Exchange, quests, rank promotions
- **Adventure Commands**: The main exploration interface
- **ONE UI Policy**: Persistent message with button-based navigation

## Environment Configuration

### Required Secrets
The bot requires two environment variables (configured via Replit Secrets):

1. **DISCORD_BOT_TOKEN**: Your bot's authentication token from Discord Developer Portal
   - Get it from: https://discord.com/developers/applications
   - Navigate to: Bot section → Copy token

2. **GUILD_ID**: Your Discord server ID (recommended but optional)
   - Enables instant slash command updates
   - Get it by: Enable Developer Mode → Right-click server → Copy Server ID

### Optional Configuration
- Database path is hardcoded to `EQ_Game.db` (local SQLite file)
- Log files stored in `logs/` directory
- All game data defined in `game_systems/data/` modules

## Running the Bot

### Automatic Startup
The workflow is configured to run automatically:
```bash
python main.py
```

### Manual Testing
Run the comprehensive test suite:
```bash
# Test database operations
python tests/test_database.py

# Test game systems
python tests/test_game_systems.py

# Run all tests
python tests/run_all_tests.py
```

### Checking Status
Monitor the Discord Bot workflow in the Replit console to see:
- Database initialization
- Cog loading
- Slash command sync
- Connection status

## Dependencies
- **discord.py**: Discord API wrapper for bot functionality
- **python-dotenv**: Environment variable management
- **cryptography**: Encryption and security utilities
- **sqlite3**: Built-in database (no separate installation needed)

## File Structure

```
eldoria-bot/
├── main.py                 # Bot entry point and initialization
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables (secrets)
├── .gitignore             # Git ignore patterns
├── README.md              # Project documentation
├── replit.md              # This file - Replit configuration
│
├── cogs/                   # Discord command handlers
│   ├── onboarding_cog.py
│   ├── character_cog.py
│   ├── guild_hub_cog.py
│   ├── quest_hub_cog.py
│   ├── adventure_commands.py
│   └── ui_helpers.py
│
├── database/               # Data layer
│   ├── database_manager.py
│   ├── create_database.py
│   └── populate_database.py
│
├── game_systems/           # Game logic
│   ├── adventure/
│   ├── combat/
│   ├── data/
│   ├── guild_system/
│   ├── items/
│   ├── monsters/
│   ├── player/
│   └── rewards/
│
├── tests/                  # Test suite
│   ├── test_database.py
│   ├── test_game_systems.py
│   └── run_all_tests.py
│
└── logs/                   # Runtime logs
    └── eldoria.log
```

## User Preferences

### Coding Style
- **ONE UI MENU Policy**: All interactions through persistent message with buttons
- **No Ephemeral Messages**: All responses are persistent
- **File Structure**: Preserve existing organization, optimize internally
- **Security First**: No hardcoded secrets, all from .env
- **Comprehensive Testing**: All changes must include test coverage

### Design Philosophy
- **Material-Based Economy**: Monsters drop materials, not coins
- **Persistent Vitals**: HP/MP persist between actions
- **Auto-Combat**: Battles play out automatically with turn delays
- **Class-Aware Narration**: Different messages for each class
- **Guild Progression**: F→SSS rank system with requirements

## Performance Optimizations

### Database
- Context managers for automatic connection cleanup
- Parameterized queries for safety and performance
- Connection timeout set to 10 seconds
- Automatic rollback on errors

### Memory Management
- Proper resource cleanup in all database operations
- No connection leaks
- Efficient JSON serialization for player stats

### Scalability
- Modular cog system for easy feature additions
- Centralized database manager
- Reusable UI components
- Singleton pattern for game data

## Troubleshooting

### Bot Won't Start
1. Check DISCORD_BOT_TOKEN is set in Replit Secrets
2. Verify token is valid in Discord Developer Portal
3. Check workflow logs for specific errors

### Database Issues
1. Delete `EQ_Game.db` to recreate fresh database
2. Run `python tests/test_database.py` to verify schema
3. Check file permissions

### Slash Commands Not Updating
1. Add GUILD_ID secret for instant updates
2. Without GUILD_ID, commands take up to 1 hour to update globally

## Future Enhancements
- Connection pooling for higher concurrency
- Redis cache for frequently accessed data
- Async database operations for better performance
- Automated backups
- Admin commands for game master controls

## Support
This is a private project. For issues:
1. Check workflow logs in Replit console
2. Run test suite to identify problems
3. Review Discord bot logs in `logs/eldoria.log`
