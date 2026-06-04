#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Filename: src/seevar_lite/state.py
Version: 0.1.0
Objective: Stateful JSON proof ledger for hardened postflight steps.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# Function: utc_now
def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


class StateLedger:
    # Function: StateLedger.__init__
    def __init__(self, out_dir: Path):
        self.out_dir = out_dir
        self.state_path = out_dir / "state.json"
        self.proof_path = out_dir / "proof.jsonl"
        self.state: dict[str, Any] = {"started_utc": utc_now(), "steps": []}

    # Function: StateLedger.write
    def write(self) -> None:
        self.out_dir.mkdir(parents=True, exist_ok=True)
        self.state_path.write_text(json.dumps(self.state, indent=2, sort_keys=True), encoding="utf-8")

    # Function: StateLedger.record
    def record(
        self,
        step: str,
        status: str,
        target: str | None = None,
        evidence: str | None = None,
        reason: str | None = None,
        extra: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        row = {
            "timestamp_utc": utc_now(),
            "step": step,
            "status": status,
            "target": target,
            "evidence": evidence,
            "reason": reason,
        }
        if extra:
            row.update(extra)
        self.out_dir.mkdir(parents=True, exist_ok=True)
        with self.proof_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
        self.state["steps"].append(row)
        self.write()
        return row
