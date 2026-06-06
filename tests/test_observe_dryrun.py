#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Filename: tests/test_observe_dryrun.py
Version: 0.1.0
Objective: Verify simulated observing dry-run proof rows.
"""

from __future__ import annotations

import json

from seevar_lite.observe_dryrun import OBSERVING_STEPS, run_observing_dryrun


# Function: test_observing_dryrun_records_all_steps_for_three_targets
def test_observing_dryrun_records_all_steps_for_three_targets(tmp_path):
    plan = {
        "targets": [
            {"name": "Target 1", "ra_deg": 1.0, "dec_deg": 2.0},
            {"name": "Target 2", "ra_deg": 3.0, "dec_deg": 4.0},
            {"name": "Target 3", "ra_deg": 5.0, "dec_deg": 6.0},
            {"name": "Target 4", "ra_deg": 7.0, "dec_deg": 8.0},
        ]
    }
    plan_path = tmp_path / "nightly_plan.json"
    plan_path.write_text(json.dumps(plan), encoding="utf-8")

    summary = run_observing_dryrun(plan_path, tmp_path / "out", max_targets=3, frames=2)

    rows = [json.loads(line) for line in (tmp_path / "out" / "proof.jsonl").read_text().splitlines()]
    observed = [row for row in rows if row["target"]]
    assert summary["target_count"] == 3
    assert len(observed) == 3 * len(OBSERVING_STEPS)
    assert {row["step"] for row in observed} == set(OBSERVING_STEPS)
    assert all(row["status"] == "pass" for row in observed)
