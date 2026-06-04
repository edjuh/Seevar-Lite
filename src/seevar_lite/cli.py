#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Filename: src/seevar_lite/cli.py
Version: 0.1.0
Objective: Command-line entry points for Seevar-Lite.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from seevar_lite.pipeline import run_postflight


# Function: main
def main() -> int:
    parser = argparse.ArgumentParser(description="Run Seevar-Lite AAVSO postflight.")
    parser.add_argument("--frames", type=Path, required=True)
    parser.add_argument("--targets", type=Path, required=True)
    parser.add_argument("--comparisons", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    state = run_postflight(
        args.frames.expanduser().resolve(),
        args.targets.expanduser().resolve(),
        args.comparisons.expanduser().resolve(),
        args.out.expanduser().resolve(),
    )
    print(json.dumps({"state": str(args.out / "state.json"), "steps": len(state.get("steps", []))}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
