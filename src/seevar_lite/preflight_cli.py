#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Filename: src/seevar_lite/preflight_cli.py
Version: 0.1.0
Objective: Command-line entry point for Seevar-Lite preflight planning.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from seevar_lite.preflight import build_nightly_plan


# Function: main
def main() -> int:
    parser = argparse.ArgumentParser(description="Build Seevar-Lite nightly AAVSO plan.")
    parser.add_argument("--objects", type=Path, required=True)
    parser.add_argument("--site", type=Path, required=True)
    parser.add_argument("--weather", type=Path, required=True)
    parser.add_argument("--ledger", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--start-utc")
    parser.add_argument("--end-utc")
    parser.add_argument("--min-alt-deg", type=float, default=30.0)
    parser.add_argument("--sun-alt-limit", type=float, default=-12.0)
    parser.add_argument("--max-targets", type=int, default=25)
    args = parser.parse_args()

    plan = build_nightly_plan(
        args.objects.expanduser().resolve(),
        args.site.expanduser().resolve(),
        args.weather.expanduser().resolve(),
        args.out.expanduser().resolve(),
        args.ledger.expanduser().resolve() if args.ledger else None,
        args.start_utc,
        args.end_utc,
        args.min_alt_deg,
        args.sun_alt_limit,
        args.max_targets,
    )
    print(json.dumps({"out": str(args.out / "nightly_plan.json"), "targets": len(plan.get("targets", []))}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
