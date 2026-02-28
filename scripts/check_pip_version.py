#!/usr/bin/env python3
"""
Security Utility: Check installed pip version.

Verifies that the installed pip version is not the vulnerable 25.3.
"""
import sys
import pip

def check_pip_version():
    """Check installed pip version for known vulnerabilities."""
    version = pip.__version__
    print(f"Detected pip version: {version}")

    if version == "25.3":
        print("CRITICAL: Vulnerable pip version 25.3 detected! (CVE-2026-1703)")
        sys.exit(1)

    print("✅ Pip version is safe.")
    sys.exit(0)

if __name__ == "__main__":
    check_pip_version()
