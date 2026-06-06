#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Filename: src/seevar_lite/seestar_alp_cli.py
Version: 0.1.0
Objective: Command-line exporter for seestar_alp schedules.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from seevar_lite.seestar_alp import export_seestar_alp_schedule


# Function: main
def main() -> int:
    parser = argparse.ArgumentParser(description="Export a Seevar-Lite plan for seestar_alp.")
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5555)
    parser.add_argument("--device", type=int, default=1)
    parser.add_argument("--max-targets", type=int, default=3)
    parser.add_argument("--gain", type=int, default=80)
    parser.add_argument("--autofocus", action="store_true")
    args = parser.parse_args()

    result = export_seestar_alp_schedule(
        args.plan.expanduser().resolve(),
        args.out.expanduser().resolve(),
        args.host,
        args.port,
        args.device,
        args.max_targets,
        args.gain,
        args.autofocus,
    )
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
