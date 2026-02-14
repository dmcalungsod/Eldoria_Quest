#!/usr/bin/env bash
# Render build script for Eldoria Quest
set -o errexit   # exit on error

pip install --upgrade pip
pip install -r requirements.txt
