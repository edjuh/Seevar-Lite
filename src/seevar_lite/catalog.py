#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Filename: src/seevar_lite/catalog.py
Version: 0.1.0
Objective: Load target and comparison-star JSON catalogs.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class SkyObject:
    name: str
    ra_deg: float
    dec_deg: float
    mag: float | None = None


# Function: _load_json
def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


# Function: load_targets
def load_targets(path: Path) -> dict[str, SkyObject]:
    payload = _load_json(path)
    return {
        name: SkyObject(name=name, ra_deg=float(row["ra_deg"]), dec_deg=float(row["dec_deg"]))
        for name, row in payload.items()
    }


# Function: load_comparisons
def load_comparisons(path: Path) -> dict[str, list[SkyObject]]:
    payload = _load_json(path)
    result: dict[str, list[SkyObject]] = {}
    for target_name, rows in payload.items():
        result[target_name] = [
            SkyObject(
                name=str(row.get("id") or row.get("name") or f"{target_name}-comp"),
                ra_deg=float(row["ra_deg"]),
                dec_deg=float(row["dec_deg"]),
                mag=float(row["mag"]),
            )
            for row in rows
        ]
    return result
