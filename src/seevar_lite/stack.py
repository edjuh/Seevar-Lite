#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Filename: src/seevar_lite/stack.py
Version: 0.1.0
Objective: Median stack same-target FITS frames while preserving WCS headers.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from astropy.io import fits

from seevar_lite.fits_io import read_fits_image


# Function: stack_frames
def stack_frames(paths: list[Path], output_path: Path) -> Path:
    if not paths:
        raise ValueError("no frames to stack")

    images = []
    header = None
    for path in paths:
        data, frame_header = read_fits_image(path)
        images.append(data)
        if header is None:
            header = frame_header.copy()

    stack = np.median(np.stack(images, axis=0), axis=0)
    assert header is not None
    header["NCOMBINE"] = len(paths)
    header["SLITE"] = "stack"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fits.writeto(output_path, stack.astype("float32"), header, overwrite=True)
    return output_path
