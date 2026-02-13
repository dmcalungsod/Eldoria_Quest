"""
Master Test Runner for Eldoria Quest
-------------------------------------
Runs all test suites and provides comprehensive test coverage.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import test_database
import test_game_systems
import test_infirmary_security
import test_security


def main():
    """Run all test suites."""
    print("\n" + "=" * 70)
    print(" " * 15 + "ELDORIA QUEST - COMPREHENSIVE TEST SUITE")
    print("=" * 70)

    print("\n\nThis will test:")
    print("  • Database operations and schema")
    print("  • Player creation and management")
    print("  • Inventory and equipment systems")
    print("  • Combat and damage calculations")
    print("  • Level-up and progression systems")
    print("  • Security and sanitization")
    print("  • Infirmary Security")
    print("\n")

    all_passed = True

    print("\n" + "-" * 70)
    print("RUNNING DATABASE TESTS")
    print("-" * 70)
    db_passed = test_database.run_all_tests()
    all_passed = all_passed and db_passed

    print("\n" + "-" * 70)
    print("RUNNING GAME SYSTEMS TESTS")
    print("-" * 70)
    game_passed = test_game_systems.run_all_tests()
    all_passed = all_passed and game_passed

    print("\n" + "-" * 70)
    print("RUNNING SECURITY TESTS")
    print("-" * 70)
    security_passed = test_security.run_all_tests()
    all_passed = all_passed and security_passed

    print("\n" + "-" * 70)
    print("RUNNING INFIRMARY SECURITY TESTS")
    print("-" * 70)
    infirmary_passed = test_infirmary_security.run_all_tests()
    all_passed = all_passed and infirmary_passed

    print("\n" + "=" * 70)
    print("FINAL TEST SUMMARY")
    print("=" * 70)
    print(f"Database Tests: {'✓ PASSED' if db_passed else '✗ FAILED'}")
    print(f"Game Systems Tests: {'✓ PASSED' if game_passed else '✗ FAILED'}")
    print(f"Security Tests: {'✓ PASSED' if security_passed else '✗ FAILED'}")
    print(f"Infirmary Security Tests: {'✓ PASSED' if infirmary_passed else '✗ FAILED'}")
    print("\n" + ("=" * 70))

    if all_passed:
        print("\n🎉 ALL TESTS PASSED! Your bot is ready for adventure! 🎉\n")
        return 0
    else:
        print("\n⚠️  SOME TESTS FAILED. Please review the errors above. ⚠️\n")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
