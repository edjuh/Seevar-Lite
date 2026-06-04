#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Filename: tests/test_postflight_pipeline.py
Version: 0.1.0
Objective: Verify the clean AAVSO postflight chain on synthetic FITS frames.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from astropy.coordinates import SkyCoord
from astropy.io import fits
from astropy.wcs import WCS
import astropy.units as u

from seevar_lite.pipeline import run_postflight


# Function: _wcs_header
def _wcs_header() -> fits.Header:
    wcs = WCS(naxis=2)
    wcs.wcs.crpix = [64, 64]
    wcs.wcs.cdelt = [-0.0002777778, 0.0002777778]
    wcs.wcs.crval = [224.44, 40.73]
    wcs.wcs.ctype = ["RA---TAN", "DEC--TAN"]
    header = wcs.to_header()
    header["OBJECT"] = "ST Boo"
    header["EXPTIME"] = 10.0
    header["FILTER"] = "V"
    header["DATE-OBS"] = "2026-06-01T22:00:00"
    return header


# Function: _add_star
def _add_star(image: np.ndarray, wcs: WCS, ra_deg: float, dec_deg: float, flux: float) -> None:
    coord = SkyCoord(ra_deg * u.deg, dec_deg * u.deg, frame="icrs")
    x0, y0 = wcs.world_to_pixel(coord)
    yy, xx = np.indices(image.shape, dtype=float)
    image += flux * np.exp(-((xx - float(x0)) ** 2 + (yy - float(y0)) ** 2) / (2 * 1.5**2))


# Function: _write_frame
def _write_frame(path: Path, offset: float = 0.0) -> None:
    header = _wcs_header()
    wcs = WCS(header)
    image = np.full((128, 128), 1000.0 + offset, dtype=float)
    _add_star(image, wcs, 224.44, 40.73, 5000)
    _add_star(image, wcs, 224.435, 40.727, 9000)
    _add_star(image, wcs, 224.445, 40.733, 6500)
    fits.writeto(path, image.astype("float32"), header, overwrite=True)


# Function: _write_json
def _write_json(path: Path, payload: dict) -> Path:
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


# Function: test_run_postflight_writes_stack_proof_and_aavso_report
def test_run_postflight_writes_stack_proof_and_aavso_report(tmp_path):
    frames = tmp_path / "frames"
    frames.mkdir()
    _write_frame(frames / "st_boo_001.fits")
    _write_frame(frames / "st_boo_002.fits", offset=2.0)
    targets = _write_json(tmp_path / "targets.json", {"ST Boo": {"ra_deg": 224.44, "dec_deg": 40.73}})
    comps = _write_json(
        tmp_path / "comparisons.json",
        {
            "ST Boo": [
                {"id": "C1", "ra_deg": 224.435, "dec_deg": 40.727, "mag": 12.3},
                {"id": "C2", "ra_deg": 224.445, "dec_deg": 40.733, "mag": 12.8},
            ]
        },
    )
    out_dir = tmp_path / "out"

    state = run_postflight(frames, targets, comps, out_dir)

    assert (out_dir / "state.json").exists()
    assert (out_dir / "proof.jsonl").exists()
    assert (out_dir / "stacks" / "ST_Boo_stack.fits").exists()
    report = out_dir / "reports" / "aavso_extended.txt"
    assert report.exists()
    text = report.read_text(encoding="utf-8")
    assert "#TYPE=EXTENDED" in text
    assert "ST Boo," in text
    assert state["steps"][-1]["step"] == "report"
    assert state["steps"][-1]["status"] == "pass"
