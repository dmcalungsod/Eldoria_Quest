#!/usr/bin/env bash
# Render build script for Eldoria Quest
set -o errexit   # exit on error

# SECURITY: Upgrade pip to fix Critical Vulnerability CVE-2026-1703
pip install --upgrade pip
pip install -r requirements.txt
