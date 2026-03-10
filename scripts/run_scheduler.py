#!/usr/bin/env python3
"""Entry point for the launchd-managed scheduler process.

Called by the launchd plist. Loads .env, then starts the blocking scheduler.
"""
import sys
from pathlib import Path

# Ensure repo root is on PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.ingestion.scheduler import start_scheduler

if __name__ == "__main__":
    start_scheduler()
