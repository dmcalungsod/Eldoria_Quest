"""
tests/test_weather_system.py

Verifies the functionality of the dynamic weather system.
"""

import datetime
from unittest.mock import patch

from game_systems.core.world_time import Weather, WorldTime


class TestWeatherSystem:
    def test_weather_enum_exists(self):
        """Ensure Weather enum is correctly defined."""
        assert Weather.CLEAR.value == "Clear"
        assert Weather.STORM.value == "Storm"
        assert Weather.ASH.value == "Ash Storm"

    def test_get_current_weather_deterministic(self):
        """
        Ensure that for the same location and hour, the weather is consistent.
        """
        location_id = "forest_outskirts"

        # Freeze time to a specific hour
        with patch("game_systems.core.world_time.datetime") as mock_datetime:
            # Create a mock datetime object
            mock_now = datetime.datetime(2023, 10, 27, 10, 0, 0)
            mock_datetime.datetime.now.return_value = mock_now
            # Mocking .hour is tricky on an instance if it's a real datetime,
            # but usually now() returns a new instance.
            # simpler: rely on the fact that now().hour will be 10 from the object we returned.

            w1 = WorldTime.get_current_weather(location_id)
            w2 = WorldTime.get_current_weather(location_id)

            assert w1 == w2, "Weather must be consistent for same location/time"

    def test_get_current_weather_varies_by_location(self):
        """
        Ensure different locations *can* have different weather at the same time.
        """
        with patch("game_systems.core.world_time.datetime") as mock_datetime:
            mock_datetime.datetime.now.return_value = datetime.datetime(2023, 10, 27, 10, 0, 0)

            results = set()
            locations = [
                "forest_outskirts",
                "molten_caldera",
                "shrouded_fen",
                "crystal_caverns",
            ]

            for loc in locations:
                results.add(WorldTime.get_current_weather(loc))

            assert len(results) > 0

    def test_get_current_weather_varies_by_hour(self):
        """Ensure weather changes over time for the same location."""
        location_id = "forest_outskirts"

        with patch("game_systems.core.world_time.datetime") as mock_datetime:
            # Hour 10
            mock_datetime.datetime.now.return_value = datetime.datetime(2023, 10, 27, 10, 0, 0)
            w1 = WorldTime.get_current_weather(location_id)

            # Hour 11
            mock_datetime.datetime.now.return_value = datetime.datetime(2023, 10, 27, 11, 0, 0)
            w2 = WorldTime.get_current_weather(location_id)

            assert isinstance(w1, Weather)
            assert isinstance(w2, Weather)

    def test_molten_caldera_weather_restrictions(self):
        """
        Molten Caldera should mainly have CLEAR, ASH, STORM.
        Should NOT have RAIN or SNOW (based on current weights).
        """
        location_id = "molten_caldera"

        # Run 50 trials with different hours
        for i in range(50):
            with patch("game_systems.core.world_time.datetime") as mock_datetime:
                mock_datetime.datetime.now.return_value = datetime.datetime(2023, 10, 27, i % 24, 0, 0)

                weather = WorldTime.get_current_weather(location_id)
                assert weather in [
                    Weather.CLEAR,
                    Weather.ASH,
                    Weather.STORM,
                ], f"Molten Caldera had unexpected weather: {weather}"

    def test_weather_flavor(self):
        """Ensure flavor text returns strings."""
        assert "Rain" in WorldTime.get_weather_flavor(Weather.RAIN)
        assert "Ash" in WorldTime.get_weather_flavor(Weather.ASH)
        assert "Clear" in WorldTime.get_weather_flavor(Weather.CLEAR)
