#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Filename: src/seevar_lite/observe_dryrun.py
Version: 0.1.0
Objective: Simulate the full observing proof chain without controlling hardware.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from seevar_lite.state import StateLedger


OBSERVING_STEPS = (
    "connect",
    "slew",
    "solve",
    "track",
    "expose",
    "accept",
    "stack",
    "photometry",
    "report",
)


# Function: load_plan
def load_plan(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


# Function: evidence_path
def evidence_path(out_dir: Path, target_name: str, step: str) -> Path:
    safe_name = target_name.replace(" ", "_").replace("/", "_")
    evidence_dir = out_dir / "evidence" / safe_name
    evidence_dir.mkdir(parents=True, exist_ok=True)
    return evidence_dir / f"{step}.json"


# Function: write_step_evidence
def write_step_evidence(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


# Function: simulate_target
def simulate_target(proof: StateLedger, out_dir: Path, target: dict[str, Any], frames: int) -> None:
    name = str(target["name"])
    for step in OBSERVING_STEPS:
        evidence = evidence_path(out_dir, name, step)
        payload = {
            "mode": "dry_run",
            "step": step,
            "target": name,
            "ra_deg": target.get("ra_deg"),
            "dec_deg": target.get("dec_deg"),
            "frames": frames if step in {"expose", "accept", "stack"} else None,
        }
        write_step_evidence(evidence, payload)
        proof.record(
            step,
            "pass",
            target=name,
            evidence=str(evidence),
            extra={"frame_count": frames} if step in {"expose", "accept", "stack"} else None,
        )


# Function: run_observing_dryrun
def run_observing_dryrun(plan_path: Path, out_dir: Path, max_targets: int = 3, frames: int = 3) -> dict[str, Any]:
    plan = load_plan(plan_path)
    targets = list(plan.get("targets", []))[:max_targets]
    proof = StateLedger(out_dir)
    proof.record("plan_load", "pass", evidence=str(plan_path), extra={"target_count": len(targets)})
    for target in targets:
        simulate_target(proof, out_dir, target, frames)
    summary_path = out_dir / "observing_dryrun_summary.json"
    summary = {
        "mode": "dry_run",
        "target_count": len(targets),
        "frames_per_target": frames,
        "targets": [target.get("name") for target in targets],
        "proof": str(proof.proof_path),
    }
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    proof.record("summary", "pass", evidence=str(summary_path), extra={"target_count": len(targets)})
    return summary
