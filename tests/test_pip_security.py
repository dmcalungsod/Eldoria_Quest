"""
Security Test Suite - Pip Version
---------------------------------
Verifies that the runtime environment is not using a vulnerable pip version.
CVE-2026-1703 affects pip 25.3.
"""

import subprocess
import unittest


class TestPipSecurity(unittest.TestCase):
    def test_pip_version_is_safe(self):
        """Verify that pip version is not 25.3 (CVE-2026-1703)."""
        # Get pip version directly from the environment to avoid import path issues
        version_output = subprocess.check_output(["python", "-m", "pip", "--version"]).decode("utf-8")
        version = version_output.split()[1]
        print(f"Testing pip version: {version}")

        # Assert version is not the specific vulnerable one
        self.assertNotEqual(version, "25.3", f"CRITICAL: Vulnerable pip version {version} detected!")

        # Ideally we want < 25.3 or > 25.3, but for now we just block the known bad one.
        # The build script pins to 24.0.


if __name__ == "__main__":
    unittest.main()
