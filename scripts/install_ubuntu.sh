#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
command -v apt-get >/dev/null || { echo 'Ubuntu/Debian only' >&2; exit 1; }
sudo apt-get update
sudo apt-get install -y bluez rfkill adb python3-venv python3-pip
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -e ".[dev]"
.venv/bin/python -m unittest discover -s tests -v
echo "Launch: $ROOT/.venv/bin/toretto-bt-auditor"
