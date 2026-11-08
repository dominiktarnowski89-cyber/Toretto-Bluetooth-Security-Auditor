#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ ! -x .venv/bin/python ]]; then
  echo "Missing .venv; run scripts/install_ubuntu.sh first." >&2
  exit 1
fi
exec .venv/bin/python -m toretto_bluetooth_auditor.collectors.hci_capture "$@"
