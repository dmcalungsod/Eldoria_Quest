import os
import sys

import pytest

# Add repo root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # noqa: E402

from game_systems.player.player_stats import calculate_practice_threshold


def test_calculate_practice_threshold():
    """Verify threshold scaling formula."""
    # Formula: 100 + (current * 5)
    assert calculate_practice_threshold(1) == 105
    assert calculate_practice_threshold(10) == 150
    assert calculate_practice_threshold(20) == 200
    assert calculate_practice_threshold(100) == 600


def test_practice_growth_single_level():
    """Verify simple level up logic."""
    current_val = 1  # Base stat
    current_exp_val = 0  # Current exp

    gain = 200  # XP gain

    # Threshold at 1: 105
    # 200 > 105 -> Level up!
    # Remaining: 95
    # Stat becomes 2
    # Threshold at 2: 110
    # 95 < 110 -> Stop.

    current_exp_val += gain
    levels_gained = 0

    while True:
        threshold = calculate_practice_threshold(current_val)
        if current_exp_val >= threshold:
            current_exp_val -= threshold
            levels_gained += 1
            current_val += 1
        else:
            break

    assert levels_gained == 1
    assert current_val == 2
    assert current_exp_val == 95


def test_practice_growth_multi_level():
    """Verify multi-level growth correctly updates threshold each step."""
    current_val = 1
    current_exp_val = 0

    # Thresholds:
    # Level 1: 105
    # Level 2: 110
    # Level 3: 115
    # Total needed for 3 levels: 105 + 110 + 115 = 330

    gain = 340  # 330 + 10 remainder
    current_exp_val += gain
    levels_gained = 0

    iteration_limit = 100
    iterations = 0

    while True:
        threshold = calculate_practice_threshold(current_val)
        if current_exp_val >= threshold:
            current_exp_val -= threshold
            levels_gained += 1
            current_val += 1
        else:
            break

        iterations += 1
        if iterations > iteration_limit:
            pytest.fail("Infinite loop detected in growth logic")

    assert levels_gained == 3
    assert current_val == 4
    assert current_exp_val == 10
