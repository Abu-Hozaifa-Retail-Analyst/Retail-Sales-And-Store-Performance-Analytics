#!/usr/bin/env sh
# Rebuild everything from scratch
set -e
python python/scripts/01_generate_data.py
python python/scripts/02_analysis.py
python python/scripts/03_scenarios.py
python python/scripts/04_build_dashboard.py
