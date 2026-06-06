#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Filename: src/seevar_lite/observe_dryrun_cli.py
Version: 0.1.0
Objective: Command-line entry point for simulated observing dry-runs.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from seevar_lite.observe_dryrun import run_observing_dryrun


# Function: main
def main() -> int:
    parser = argparse.ArgumentParser(description="Run a proof-only Seevar-Lite observing dry-run.")
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--max-targets", type=int, default=3)
    parser.add_argument("--frames", type=int, default=3)
    args = parser.parse_args()

    summary = run_observing_dryrun(
        args.plan.expanduser().resolve(),
        args.out.expanduser().resolve(),
        args.max_targets,
        args.frames,
    )
    print(json.dumps({"out": str(args.out), **summary}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
