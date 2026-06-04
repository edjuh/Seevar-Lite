#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Filename: src/seevar_lite/fits_io.py
Version: 0.1.0
Objective: FITS loading and target grouping helpers.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import numpy as np
from astropy.io import fits


# Function: fits_files
def fits_files(path: Path) -> list[Path]:
    if path.is_file():
        return [path]
    return sorted(
        item
        for item in path.rglob("*")
        if item.is_file() and item.suffix.lower() in {".fit", ".fits", ".fts"}
    )


# Function: read_fits_image
def read_fits_image(path: Path) -> tuple[np.ndarray, fits.Header]:
    with fits.open(path, memmap=False) as hdul:
        data = np.asarray(hdul[0].data, dtype=float)
        header = hdul[0].header.copy()
    if data.ndim == 3:
        data = np.mean(data, axis=0)
    if data.ndim != 2:
        raise ValueError(f"{path} is not a 2D image")
    return data, header


# Function: object_name
def object_name(header: fits.Header, fallback: str) -> str:
    name = str(header.get("OBJECT") or "").strip()
    return name or fallback


# Function: group_by_object
def group_by_object(paths: Iterable[Path]) -> dict[str, list[Path]]:
    groups: dict[str, list[Path]] = {}
    for path in paths:
        _, header = read_fits_image(path)
        groups.setdefault(object_name(header, path.stem.split("_")[0]), []).append(path)
    return groups
