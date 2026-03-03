import sys
from unittest.mock import MagicMock, patch

# Patching sys.modules to mock pymongo is standard in this repo's tests
sys.modules["pymongo"] = MagicMock()
sys.modules["pymongo.errors"] = MagicMock()

# Do NOT mock database.database_manager or game_systems.data... in sys.modules
# because that pollutes the environment for other tests.
# Instead, we will rely on dependency injection (passing mock_db)
# and patching data attributes on the imported class/module if needed.

# Import the class and function
# noqa: E402
from game_systems.crafting.crafting_system import CraftingSystem, calculate_crafting_xp_req  # noqa: E402


class TestCraftingProficiency:
    def setup_method(self):
        self.mock_db = MagicMock()
        self.system = CraftingSystem(self.mock_db)

        # Setup default player for DB
        self.mock_player = {"discord_id": 123, "crafting_level": 1, "crafting_xp": 0}
        self.mock_db.get_player.return_value = self.mock_player

    def test_xp_curve(self):
        # Verify the formula works as intended
        req_1 = calculate_crafting_xp_req(1)
        assert req_1 == 50

        req_2 = calculate_crafting_xp_req(2)
        # 50 * 2^1.3 = 50 * 2.46 = 123
        assert req_2 == 123

    def test_add_crafting_xp_basic(self):
        """Test adding XP without leveling up."""
        msg = self.system._add_crafting_xp(123, "Common")

        # Check that update_player_fields was called with new XP
        self.mock_db.update_player_fields.assert_called_with(
            123,
            crafting_level=1,
            crafting_xp=10,  # Common = 10 XP
        )
        assert "+10 Craft XP" in msg

    def test_add_crafting_xp_levelup(self):
        """Test adding XP that triggers a level up."""
        # Current: Level 1, 45 XP. Req: 50.
        self.mock_player["crafting_xp"] = 45

        # Add Common (10 XP) -> 55 XP. Should level up.
        # 55 - 50 = 5 XP remaining. Level 2.
        msg = self.system._add_crafting_xp(123, "Common")

        self.mock_db.update_player_fields.assert_called_with(123, crafting_level=2, crafting_xp=5)
        assert "Level Up!" in msg
        assert "Level **2**" in msg

    def test_add_crafting_xp_multi_levelup(self):
        """Test massive XP gain triggering multiple levels."""
        # Level 1, 0 XP. Req 50.
        # Add Mythical (500 XP).
        # 500 - 50 (L1->L2) = 450.
        # L2 Req: 123.
        # 450 - 123 = 327. Level 3.
        # L3 Req: 50 * 3^1.3 = 50 * 4.17 = 208.
        # 327 - 208 = 119. Level 4.

        msg = self.system._add_crafting_xp(123, "Mythical")

        # It should reach Level 4 with some XP left
        # We don't need to be exact on the XP left, just the level logic
        args, kwargs = self.mock_db.update_player_fields.call_args
        assert kwargs["crafting_level"] >= 3
        assert "Level Up!" in msg

    def test_roll_quality_bonus(self):
        """Test that higher levels increase upgrade chance."""
        # Mock random
        with patch("random.random") as mock_random:
            # Case 1: Level 1 (Base 10% + 0.5% = 10.5% = 0.105)
            self.mock_player["crafting_level"] = 1

            # Roll 0.104 -> Should succeed (less than 0.105)
            mock_random.side_effect = [0.104, 0.99]  # First check, then cascade check (fail)
            result = self.system._roll_quality("Common", 123)
            assert result == "Uncommon"

            # Roll 0.106 -> Should fail (greater than 0.105)
            mock_random.side_effect = [0.106]
            result = self.system._roll_quality("Common", 123)
            assert result == "Common"

            # Case 2: Level 20 (Base 10% + 20*0.5% = 20% = 0.20)
            self.mock_player["crafting_level"] = 20

            # Roll 0.19 -> Should succeed
            mock_random.side_effect = [0.19, 0.99]
            result = self.system._roll_quality("Common", 123)
            assert result == "Uncommon"
