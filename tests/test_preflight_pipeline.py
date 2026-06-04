#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Filename: tests/test_preflight_pipeline.py
Version: 0.1.0
Objective: Verify Seevar-Lite preflight builds a hardened nightly plan.
"""

from __future__ import annotations

import json
from pathlib import Path

from seevar_lite.preflight import build_nightly_plan


# Function: _write_json
def _write_json(path: Path, payload: dict) -> Path:
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


# Function: test_build_nightly_plan_filters_weather_dark_visibility
def test_build_nightly_plan_filters_weather_dark_visibility(tmp_path):
    objects = _write_json(
        tmp_path / "objects.json",
        {
            "targets": [
                {
                    "name": "ST Boo",
                    "ra_deg": 224.44,
                    "dec_deg": 40.73,
                    "priority": 10,
                    "integration_sec": 600,
                },
                {
                    "name": "Too South",
                    "ra_deg": 10.0,
                    "dec_deg": -80.0,
                    "priority": 1,
                    "integration_sec": 600,
                },
            ]
        },
    )
    site = _write_json(tmp_path / "site.json", {"lat": 52.3821, "lon": 4.60154, "elevation_m": 5})
    weather = _write_json(tmp_path / "weather.json", {"unsafe": False, "cloud_pct": 10})
    out_dir = tmp_path / "out"

    plan = build_nightly_plan(
        objects,
        site,
        weather,
        out_dir,
        start_utc="2026-06-04T20:00:00Z",
        end_utc="2026-06-05T03:00:00Z",
        min_alt_deg=20.0,
    )

    assert (out_dir / "nightly_plan.json").exists()
    assert (out_dir / "state.json").exists()
    assert (out_dir / "proof.jsonl").exists()
    assert [target["name"] for target in plan["targets"]] == ["ST Boo"]
    assert plan["targets"][0]["recommended_order"] == 1
    assert plan["metadata"]["weather"] == "ok"


# Function: test_build_nightly_plan_stops_on_bad_weather
def test_build_nightly_plan_stops_on_bad_weather(tmp_path):
    objects = _write_json(tmp_path / "objects.json", {"targets": []})
    site = _write_json(tmp_path / "site.json", {"lat": 52.3821, "lon": 4.60154})
    weather = _write_json(tmp_path / "weather.json", {"unsafe": True})

    plan = build_nightly_plan(
        objects,
        site,
        weather,
        tmp_path / "out",
        start_utc="2026-06-04T20:00:00Z",
        end_utc="2026-06-05T03:00:00Z",
    )

    assert plan["targets"] == []
    assert plan["metadata"]["weather"] == "weather_unsafe"
