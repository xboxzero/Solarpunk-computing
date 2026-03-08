#!/bin/bash
# Quick connect to the Solarpunk terminal server
# Usage: ./connect.sh [destination_hash]

DEST="${1:-90ab7e811885bb83a39255211d8d5c3e}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

exec python3 "$SCRIPT_DIR/terminal_client.py" "$DEST"
