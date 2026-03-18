#!/usr/bin/env python3
"""
cadence -- Install MCP datetime server config.

Generates or merges a .mcp.json in the user's home directory with
the correct absolute path to mcp/datetime-server.py.

Usage:
    python install_mcp.py
"""

import json
import os
import sys
from pathlib import Path

MCP_FILENAME = ".mcp.json"
SERVER_NAME = "cadence-datetime"


def main() -> None:
    # Resolve absolute path to datetime-server.py
    script_dir = Path(__file__).resolve().parent
    datetime_server = script_dir / "datetime-server.py"

    if not datetime_server.is_file():
        print(f"ERROR: datetime-server.py not found at {datetime_server}", file=sys.stderr)
        sys.exit(1)

    mcp_path = Path.home() / MCP_FILENAME

    # Build our server entry
    server_entry = {
        "command": sys.executable,
        "args": [str(datetime_server)],
        "env": {},
    }

    # Load or create the config
    existing = {}
    if mcp_path.is_file():
        try:
            with open(mcp_path, "r", encoding="utf-8") as f:
                existing = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            print(f"WARNING: Could not parse existing {mcp_path}: {e}")
            print(f"  The file will be backed up and replaced.")
            backup = mcp_path.with_suffix(".mcp.json.bak")
            os.rename(mcp_path, backup)
            print(f"  Backup saved to {backup}")
            existing = {}

    if "mcpServers" not in existing:
        existing["mcpServers"] = {}

    # Check if entry already exists
    if SERVER_NAME in existing["mcpServers"]:
        current = existing["mcpServers"][SERVER_NAME]
        if current == server_entry:
            print(f"MCP config already up to date in {mcp_path}")
            print(f"  Server: {SERVER_NAME}")
            print(f"  Path:   {datetime_server}")
            return

        print(f"Existing '{SERVER_NAME}' entry found in {mcp_path}:")
        print(f"  Current: {json.dumps(current, indent=2)}")
        print(f"  New:     {json.dumps(server_entry, indent=2)}")
        confirm = input("Overwrite? [y/N] ").strip().lower()
        if confirm != "y":
            print("Aborted.")
            return

    # If file exists with other servers, confirm merge
    other_servers = {k: v for k, v in existing.get("mcpServers", {}).items() if k != SERVER_NAME}
    if mcp_path.is_file() and other_servers:
        print(f"Found existing {mcp_path} with {len(other_servers)} other server(s):")
        for name in other_servers:
            print(f"  - {name}")
        print(f"Will add '{SERVER_NAME}' alongside them.")
        confirm = input("Continue? [y/N] ").strip().lower()
        if confirm != "y":
            print("Aborted.")
            return
    elif not mcp_path.is_file():
        print(f"Will create new {mcp_path}")
        confirm = input("Continue? [y/N] ").strip().lower()
        if confirm != "y":
            print("Aborted.")
            return

    existing["mcpServers"][SERVER_NAME] = server_entry

    with open(mcp_path, "w", encoding="utf-8") as f:
        json.dump(existing, f, indent=2)
        f.write("\n")

    print()
    print(f"MCP config written to {mcp_path}")
    print(f"  Server: {SERVER_NAME}")
    print(f"  Command: {sys.executable} {datetime_server}")
    print()
    print("Restart your MCP client (e.g., Claude Code) to pick up the change.")


if __name__ == "__main__":
    main()
