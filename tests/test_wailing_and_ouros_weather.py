import pytest
from game_systems.core.world_time import WorldTime, Weather

def test_new_locations_weather():
    weather_wailing = WorldTime.get_current_weather("the_wailing_chasm")
    weather_ouros = WorldTime.get_current_weather("silent_city_ouros")

    assert weather_wailing in [Weather.MIASMA, Weather.FOG, Weather.CLEAR]
    assert weather_ouros in [Weather.CLEAR, Weather.FOG, Weather.ASH]
