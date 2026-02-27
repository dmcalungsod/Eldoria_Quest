#!/usr/bin/env bash
# Render build script for Eldoria Quest
set -o errexit   # exit on error

# SECURITY: Pin pip to safe version to avoid Critical Vulnerability CVE-2026-1703 (present in 25.3)
pip install "pip==24.0"
pip install -r requirements.txt
