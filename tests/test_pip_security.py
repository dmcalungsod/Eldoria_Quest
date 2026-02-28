"""
Security Test Suite - Pip Version
---------------------------------
Verifies that the runtime environment is not using a vulnerable pip version.
CVE-2026-1703 affects pip 25.3.
"""

import pip


def test_pip_version_is_safe():
    """Verify that pip version is not 25.3 (CVE-2026-1703)."""
    version = pip.__version__
    print(f"Testing pip version: {version}")

    # Assert version is not the specific vulnerable one
    assert version != "25.3", f"CRITICAL: Vulnerable pip version {version} detected!"

    # Ideally we want < 25.3 or > 25.3, but for now we just block the known bad one.
    # The build script pins to 24.0.
