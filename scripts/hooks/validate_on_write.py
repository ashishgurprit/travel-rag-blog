#!/usr/bin/env python3
"""Post-write validation hook for Claude Code.

Runs lightweight syntax checks on files that were just written or edited.
Called by the PostToolUse hook for Write|Edit tool calls.

Reads the tool input from stdin as JSON (Claude Code hook protocol).
Exits 0 on success, 1 on validation failure (blocks the tool call result).
"""

import ast
import json
import sys
from pathlib import Path


def _check_python(path):
    try:
        source = path.read_text(encoding="utf-8")
        ast.parse(source, filename=str(path))
        return []
    except SyntaxError as e:
        return [f"SyntaxError in {path}: {e}"]
    except Exception as e:
        return [f"Could not read {path}: {e}"]


def _check_json(path):
    try:
        json.loads(path.read_text(encoding="utf-8"))
        return []
    except json.JSONDecodeError as e:
        return [f"JSONDecodeError in {path}: {e}"]
    except Exception as e:
        return [f"Could not read {path}: {e}"]


def main():
    try:
        raw = sys.stdin.read()
        data = json.loads(raw) if raw.strip() else {}
    except Exception:
        data = {}

    file_path = data.get("file_path", "")
    if not file_path:
        return 0

    path = Path(file_path)
    if not path.exists():
        return 0

    errors = []
    if path.suffix == ".py":
        errors.extend(_check_python(path))
    elif path.suffix == ".json":
        errors.extend(_check_json(path))

    if errors:
        for err in errors:
            print(f"[validate_on_write] {err}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
