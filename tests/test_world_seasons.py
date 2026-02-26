import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime
from game_systems.core.world_time import WorldTime, TimePhase, Weather, Season, LOCATION_WEATHER_WEIGHTS

class TestWorldSeasons(unittest.TestCase):
    """
    Tests for the Seasonal System implementation in WorldTime.
    """

    def setUp(self):
        # We patch 'game_systems.core.world_time.WorldTime.now'
        # But we need to make sure we import Season first (it might not exist yet in the actual file, so this test will fail initially if run against current code)
        pass

    @patch("game_systems.core.world_time.WorldTime.now")
    def test_get_current_season(self, mock_now):
        """Verify months map to correct seasons."""
        # Winter: Dec, Jan, Feb
        mock_now.return_value = datetime(2025, 12, 15)
        self.assertEqual(WorldTime.get_current_season(), Season.WINTER)

        mock_now.return_value = datetime(2025, 1, 15)
        self.assertEqual(WorldTime.get_current_season(), Season.WINTER)

        mock_now.return_value = datetime(2025, 2, 28)
        self.assertEqual(WorldTime.get_current_season(), Season.WINTER)

        # Spring: Mar, Apr, May
        mock_now.return_value = datetime(2025, 3, 1)
        self.assertEqual(WorldTime.get_current_season(), Season.SPRING)

        mock_now.return_value = datetime(2025, 5, 31)
        self.assertEqual(WorldTime.get_current_season(), Season.SPRING)

        # Summer: Jun, Jul, Aug
        mock_now.return_value = datetime(2025, 6, 1)
        self.assertEqual(WorldTime.get_current_season(), Season.SUMMER)

        mock_now.return_value = datetime(2025, 8, 31)
        self.assertEqual(WorldTime.get_current_season(), Season.SUMMER)

        # Autumn: Sep, Oct, Nov
        mock_now.return_value = datetime(2025, 9, 1)
        self.assertEqual(WorldTime.get_current_season(), Season.AUTUMN)

        mock_now.return_value = datetime(2025, 11, 30)
        self.assertEqual(WorldTime.get_current_season(), Season.AUTUMN)

    @patch("game_systems.core.world_time.WorldTime.now")
    @patch("random.Random")
    def test_weather_weights_seasonal(self, mock_random_cls, mock_now):
        """
        Verify that seasonal modifiers are applied to weather weights.
        We will inspect the weights passed to rng.choices.
        """
        # Mock Random instance
        mock_rng = MagicMock()
        mock_random_cls.return_value = mock_rng
        mock_rng.choices.return_value = [Weather.SNOW]  # Default return

        # 1. Test WINTER in 'frostfall_expanse' (Already Snowy)
        # Expect SNOW and BLIZZARD to be boosted
        mock_now.return_value = datetime(2025, 1, 15) # Winter

        # frostfall_expanse base: [(SNOW, 40), (BLIZZARD, 30), (CLEAR, 20), (FOG, 10)]
        # Winter Modifiers: SNOW x2.0, BLIZZARD x1.5, RAIN x0.5, CLEAR x0.8
        # Expected: SNOW=80, BLIZZARD=45, CLEAR=16, FOG=10

        WorldTime.get_current_weather("frostfall_expanse")

        # Extract arguments passed to choices
        # choices(population, weights=..., k=1)
        args, kwargs = mock_rng.choices.call_args
        population = args[0]
        weights = kwargs['weights']

        weight_map = dict(zip(population, weights))

        self.assertAlmostEqual(weight_map[Weather.SNOW], 80.0)
        self.assertAlmostEqual(weight_map[Weather.BLIZZARD], 45.0)
        self.assertAlmostEqual(weight_map[Weather.CLEAR], 16.0)
        self.assertAlmostEqual(weight_map[Weather.FOG], 10.0) # Unchanged

    @patch("game_systems.core.world_time.WorldTime.now")
    @patch("random.Random")
    def test_weather_integrity_volcano(self, mock_random_cls, mock_now):
        """
        Verify that seasons do not add impossible weather to locations.
        E.g. Winter should NOT add Snow to 'molten_caldera'.
        """
        mock_rng = MagicMock()
        mock_random_cls.return_value = mock_rng
        mock_rng.choices.return_value = [Weather.ASH]

        mock_now.return_value = datetime(2025, 1, 15) # Winter

        # molten_caldera base: [(CLEAR, 50), (ASH, 40), (STORM, 10)]
        # Even with Winter modifiers, SNOW is not in the base list, so it should not appear.

        WorldTime.get_current_weather("molten_caldera")

        args, kwargs = mock_rng.choices.call_args
        population = args[0]

        self.assertNotIn(Weather.SNOW, population)
        self.assertNotIn(Weather.BLIZZARD, population)
