#!/usr/bin/env python3
"""Cursor stop hook -> save_log.py adapter. Never writes stdout; always exits 0."""
import json
import os
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SAVE_LOG = os.path.join(ROOT, "logs", "save_log.py")


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception as exc:  # noqa: BLE001
        print(f"save_log_hook: stdin parse failed: {exc}", file=sys.stderr)
        return 0

    roots = payload.get("workspace_roots") or []
    cwd = roots[0] if roots else os.environ.get("CURSOR_PROJECT_DIR", ROOT)
    adapted = {
        "transcript_path": payload.get("transcript_path"),
        "cwd": cwd,
        "session_id": payload.get("conversation_id") or "session",
    }

    try:
        subprocess.run(
            [sys.executable, SAVE_LOG, "--tool", "cursor"],
            input=json.dumps(adapted),
            text=True,
            check=False,
            capture_output=True,
        )
    except Exception as exc:  # noqa: BLE001
        print(f"save_log_hook: invoke failed: {exc}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
