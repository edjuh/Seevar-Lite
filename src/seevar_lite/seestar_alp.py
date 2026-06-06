#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Filename: src/seevar_lite/seestar_alp.py
Version: 0.1.0
Objective: Convert Seevar-Lite plans into seestar_alp scheduler commands.
"""

from __future__ import annotations

import json
import shlex
from pathlib import Path
from typing import Any

from seevar_lite.state import StateLedger


# Function: load_plan
def load_plan(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


# Function: target_to_schedule_item
def target_to_schedule_item(target: dict[str, Any], gain: int, autofocus: bool) -> dict[str, Any]:
    return {
        "action": "start_mosaic",
        "params": {
            "target_name": target["name"],
            "ra": float(target["ra_deg"]),
            "dec": float(target["dec_deg"]),
            "is_j2000": True,
            "is_use_lp_filter": False,
            "is_use_autofocus": autofocus,
            "session_time_sec": int(target.get("integration_sec", 600)),
            "ra_num": 1,
            "dec_num": 1,
            "panel_overlap_percent": 20,
            "gain": gain,
        },
    }


# Function: ssalp_prefix
def ssalp_prefix(host: str, port: int, device: int) -> str:
    return f"ssalp --host {shlex.quote(host)} --port {port} --device {device} --output json"


# Function: command_for_item
def command_for_item(prefix: str, item: dict[str, Any]) -> str:
    params = item["params"]
    parts = [
        prefix,
        "schedule add-mosaic",
        "--target",
        shlex.quote(str(params["target_name"])),
        "--ra",
        shlex.quote(str(params["ra"])),
        "--dec",
        shlex.quote(str(params["dec"])),
        "--time",
        str(params["session_time_sec"]),
        "--panels-ra",
        str(params["ra_num"]),
        "--panels-dec",
        str(params["dec_num"]),
        "--overlap",
        str(params["panel_overlap_percent"]),
        "--gain",
        str(params["gain"]),
        "--j2000",
    ]
    if params.get("is_use_autofocus"):
        parts.append("--autofocus")
    return " ".join(parts)


# Function: export_seestar_alp_schedule
def export_seestar_alp_schedule(
    plan_path: Path,
    out_dir: Path,
    host: str,
    port: int = 5555,
    device: int = 1,
    max_targets: int = 3,
    gain: int = 80,
    autofocus: bool = False,
) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    plan = load_plan(plan_path)
    targets = list(plan.get("targets", []))[:max_targets]
    proof = StateLedger(out_dir)
    proof.record("plan_load", "pass", evidence=str(plan_path), extra={"target_count": len(targets)})

    items = [target_to_schedule_item(target, gain, autofocus) for target in targets]
    schedule = {
        "format": "seestar_alp_schedule",
        "mode": "dry_export",
        "targets": [target.get("name") for target in targets],
        "items": items,
    }
    schedule_path = out_dir / "seestar_alp_schedule.json"
    schedule_path.write_text(json.dumps(schedule, indent=2, sort_keys=True), encoding="utf-8")
    proof.record("seestar_alp_schedule_export", "pass", evidence=str(schedule_path), extra={"item_count": len(items)})

    prefix = ssalp_prefix(host, port, device)
    commands = [f"{prefix} schedule create"]
    commands.extend(command_for_item(prefix, item) for item in items)
    commands.append(f"{prefix} schedule start")
    commands_path = out_dir / "ssalp_commands.sh"
    commands_path.write_text("#!/usr/bin/env bash\nset -euo pipefail\n" + "\n".join(commands) + "\n", encoding="utf-8")
    commands_path.chmod(0o755)
    proof.record("ssalp_commands_export", "pass", evidence=str(commands_path), extra={"command_count": len(commands)})

    return {
        "target_count": len(targets),
        "schedule": str(schedule_path),
        "commands": str(commands_path),
        "proof": str(proof.proof_path),
    }
