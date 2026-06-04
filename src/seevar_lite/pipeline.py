#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Filename: src/seevar_lite/pipeline.py
Version: 0.1.0
Objective: AAVSO-first postflight pipeline with proof gates.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from seevar_lite.aavso import format_extended_row, observation_jd, write_report
from seevar_lite.catalog import load_comparisons, load_targets
from seevar_lite.fits_io import fits_files, group_by_object
from seevar_lite.photometry import measure_target
from seevar_lite.stack import stack_frames
from seevar_lite.state import StateLedger


# Function: run_postflight
def run_postflight(frames_dir: Path, targets_path: Path, comparisons_path: Path, out_dir: Path) -> dict[str, Any]:
    ledger = StateLedger(out_dir)
    targets = load_targets(targets_path)
    comparisons = load_comparisons(comparisons_path)
    ledger.record("catalog", "pass", evidence=str(targets_path), extra={"target_count": len(targets)})

    frames = fits_files(frames_dir)
    if not frames:
        ledger.record("ingest", "fail", reason="no FITS files found")
        return ledger.state
    ledger.record("ingest", "pass", evidence=str(frames_dir), extra={"frame_count": len(frames)})

    groups = group_by_object(frames)
    report_rows = []
    for target_name, paths in sorted(groups.items()):
        if target_name not in targets:
            ledger.record("target", "skip", target=target_name, reason="target missing from catalog")
            continue
        if target_name not in comparisons:
            ledger.record("target", "fail", target=target_name, reason="comparison catalog missing")
            continue

        stack_path = out_dir / "stacks" / f"{target_name.replace(' ', '_')}_stack.fits"
        try:
            stack_frames(paths, stack_path)
            ledger.record("stack", "pass", target=target_name, evidence=str(stack_path), extra={"frame_count": len(paths)})
            result = measure_target(stack_path, targets[target_name], comparisons[target_name])
            ledger.record(
                "photometry",
                "pass",
                target=target_name,
                evidence=str(stack_path),
                extra={"mag": result.mag, "err": result.err, "comp_count": result.comp_count},
            )
            report_rows.append(format_extended_row(result, observation_jd(stack_path)))
        except Exception as exc:
            ledger.record("target", "fail", target=target_name, evidence=str(stack_path), reason=str(exc))

    if not report_rows:
        ledger.record("report", "fail", reason="no accepted photometry rows")
        return ledger.state

    report_path = write_report(report_rows, out_dir / "reports" / "aavso_extended.txt")
    ledger.record("report", "pass", evidence=str(report_path), extra={"row_count": len(report_rows)})
    return ledger.state
