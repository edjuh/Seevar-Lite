#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Filename: tests/test_seestar_alp_export.py
Version: 0.1.0
Objective: Verify seestar_alp schedule export from Seevar-Lite plans.
"""

from __future__ import annotations

import json

from seevar_lite.seestar_alp import export_seestar_alp_schedule


# Function: test_export_seestar_alp_schedule_writes_schedule_and_commands
def test_export_seestar_alp_schedule_writes_schedule_and_commands(tmp_path):
    plan = {
        "targets": [
            {"name": "TT Boo", "ra_deg": 224.1, "dec_deg": 40.1, "integration_sec": 120},
            {"name": "UZ Boo", "ra_deg": 225.1, "dec_deg": 41.1, "integration_sec": 180},
            {"name": "Z Cam", "ra_deg": 126.1, "dec_deg": 73.1, "integration_sec": 240},
        ]
    }
    plan_path = tmp_path / "nightly_plan.json"
    plan_path.write_text(json.dumps(plan), encoding="utf-8")

    result = export_seestar_alp_schedule(plan_path, tmp_path / "out", "192.168.178.57", max_targets=2)

    schedule = json.loads((tmp_path / "out" / "seestar_alp_schedule.json").read_text(encoding="utf-8"))
    commands = (tmp_path / "out" / "ssalp_commands.sh").read_text(encoding="utf-8")
    assert result["target_count"] == 2
    assert [item["params"]["target_name"] for item in schedule["items"]] == ["TT Boo", "UZ Boo"]
    assert "schedule create" in commands
    assert "schedule add-mosaic --target 'TT Boo'" in commands
    assert "schedule start" in commands
