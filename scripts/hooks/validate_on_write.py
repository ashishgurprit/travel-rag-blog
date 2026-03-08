#!/usr/bin/env python3
"""
Post-write validation hook for Claude Code.
Runs after every Write or Edit tool use.
Add project-specific checks here as the codebase grows.
"""

import sys
import json
import os

def main():
    # Read hook input from stdin (Claude Code passes tool use context as JSON)
    try:
        raw = sys.stdin.read()
        data = json.loads(raw) if raw.strip() else {}
    except (json.JSONDecodeError, Exception):
        data = {}

    file_path = data.get("tool_input", {}).get("file_path", "")

    # No-op for now — placeholder for future validations such as:
    # - Lint Python files on write
    # - Check for hardcoded secrets / API keys
    # - Validate JSON/YAML syntax
    # - Enforce plan.md is not deleted

    # Exit 0 = allow the write to proceed
    sys.exit(0)

if __name__ == "__main__":
    main()
