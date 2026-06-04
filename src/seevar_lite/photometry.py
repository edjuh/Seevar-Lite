#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Filename: src/seevar_lite/photometry.py
Version: 0.1.0
Objective: WCS-backed aperture photometry for AAVSO staging.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from astropy.coordinates import SkyCoord
from astropy.io import fits
from astropy.stats import sigma_clipped_stats
from astropy.wcs import WCS
import astropy.units as u

from seevar_lite.catalog import SkyObject
from seevar_lite.fits_io import read_fits_image


@dataclass(frozen=True)
class PhotometryResult:
    target: str
    mag: float
    err: float
    comp_count: int
    exposure_sec: float
    filter_name: str


# Function: _pixel_position
def _pixel_position(wcs: WCS, obj: SkyObject) -> tuple[float, float]:
    coord = SkyCoord(obj.ra_deg * u.deg, obj.dec_deg * u.deg, frame="icrs")
    x, y = wcs.world_to_pixel(coord)
    return float(x), float(y)


# Function: _aperture_flux
def _aperture_flux(data: np.ndarray, x: float, y: float, radius: float, annulus: tuple[float, float]) -> float:
    yy, xx = np.indices(data.shape, dtype=float)
    rr = np.hypot(xx - x, yy - y)
    aperture = rr <= radius
    sky = (rr >= annulus[0]) & (rr <= annulus[1])
    if not np.any(aperture) or not np.any(sky):
        raise ValueError("aperture or sky annulus falls outside image")
    _, median_sky, _ = sigma_clipped_stats(data[sky], sigma=3.0, maxiters=5)
    return float(np.sum(data[aperture] - median_sky))


# Function: _instrumental_mag
def _instrumental_mag(flux: float, exposure_sec: float) -> float:
    if flux <= 0:
        raise ValueError("non-positive aperture flux")
    return -2.5 * math.log10(flux / max(exposure_sec, 1e-9))


# Function: measure_target
def measure_target(
    stack_path: Path,
    target: SkyObject,
    comparisons: list[SkyObject],
    aperture_radius: float = 4.0,
    annulus: tuple[float, float] = (8.0, 14.0),
    min_comps: int = 2,
) -> PhotometryResult:
    data, header = read_fits_image(stack_path)
    wcs = WCS(header)
    if not wcs.has_celestial:
        raise ValueError("stack has no celestial WCS")

    exposure_sec = float(header.get("EXPTIME") or header.get("EXPOSURE") or 1.0)
    filter_name = str(header.get("FILTER") or "V")
    target_flux = _aperture_flux(data, *_pixel_position(wcs, target), aperture_radius, annulus)
    target_inst = _instrumental_mag(target_flux, exposure_sec)

    zero_points = []
    for comp in comparisons:
        if comp.mag is None:
            continue
        comp_flux = _aperture_flux(data, *_pixel_position(wcs, comp), aperture_radius, annulus)
        comp_inst = _instrumental_mag(comp_flux, exposure_sec)
        zero_points.append(float(comp.mag) - comp_inst)

    if len(zero_points) < min_comps:
        raise ValueError(f"need at least {min_comps} valid comparison stars")

    zp = float(np.median(zero_points))
    err = float(np.std(zero_points)) if len(zero_points) > 1 else 0.0
    return PhotometryResult(
        target=target.name,
        mag=target_inst + zp,
        err=err,
        comp_count=len(zero_points),
        exposure_sec=exposure_sec,
        filter_name=filter_name,
    )
