#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Filename: src/seevar_lite/aavso.py
Version: 0.1.0
Objective: Stage AAVSO Extended format reports.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from astropy.io import fits
from astropy.time import Time

from seevar_lite.photometry import PhotometryResult


# Function: observation_jd
def observation_jd(stack_path: Path) -> float:
    header = fits.getheader(stack_path)
    date_obs = header.get("DATE-OBS")
    if date_obs:
        return float(Time(str(date_obs), format="isot", scale="utc").jd)
    return float(Time(datetime.now(timezone.utc)).jd)


# Function: format_extended_row
def format_extended_row(result: PhotometryResult, jd: float, observer_code: str = "SEEVA") -> str:
    return (
        f"{result.target},{jd:.5f},{result.mag:.3f},{result.err:.3f},"
        f"{result.filter_name},NO,{observer_code},ENSEMBLE,NA,na"
    )


# Function: write_report
def write_report(rows: list[str], output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    header = [
        "#TYPE=EXTENDED",
        "#OBSCODE=SEEVA",
        "#SOFTWARE=Seevar-Lite",
        "#DELIM=,",
        "#DATE=JD",
        "#OBSTYPE=CCD",
    ]
    output_path.write_text("\n".join(header + rows) + "\n", encoding="utf-8")
    return output_path
