#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Filename: src/seevar_lite/preflight.py
Version: 0.1.0
Objective: Build AAVSO-first nightly plans from object, weather, and dark-window JSON.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import astropy.units as u
from astropy.coordinates import AltAz, EarthLocation, SkyCoord, get_sun
from astropy.time import Time
from astropy.utils import iers

from seevar_lite.state import StateLedger

iers.conf.auto_download = False
iers.conf.auto_max_age = None


@dataclass(frozen=True)
class Site:
    lat: float
    lon: float
    elevation_m: float = 0.0


# Function: load_json
def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


# Function: parse_utc
def parse_utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


# Function: parse_site
def parse_site(payload: dict[str, Any]) -> Site:
    return Site(
        lat=float(payload["lat"]),
        lon=float(payload.get("lon", payload.get("long"))),
        elevation_m=float(payload.get("elevation_m", 0.0)),
    )


# Function: weather_allows
def weather_allows(payload: dict[str, Any]) -> tuple[bool, str]:
    if not payload:
        return True, "missing_weather_allowed"
    if bool(payload.get("unsafe", False)):
        return False, "weather_unsafe"
    if bool(payload.get("cloudy", False)):
        return False, "cloudy"
    cloud_pct = payload.get("cloud_pct")
    if cloud_pct is not None and float(cloud_pct) > float(payload.get("max_cloud_pct", 70.0)):
        return False, "cloud_pct"
    return True, "ok"


# Function: time_grid
def time_grid(start: datetime, end: datetime, step_min: int = 10) -> list[datetime]:
    if end <= start:
        raise ValueError("end must be after start")
    steps = int((end - start).total_seconds() // (step_min * 60)) + 1
    return [start + timedelta(minutes=step_min * index) for index in range(steps)]


# Function: dark_times
def dark_times(times: list[datetime], site: Site, sun_alt_limit: float = -12.0) -> list[datetime]:
    location = EarthLocation(lat=site.lat * u.deg, lon=site.lon * u.deg, height=site.elevation_m * u.m)
    astro_times = Time(times)
    sun_alt = get_sun(astro_times).transform_to(AltAz(obstime=astro_times, location=location)).alt.deg
    return [dt for dt, alt in zip(times, sun_alt, strict=True) if float(alt) <= sun_alt_limit]


# Function: target_altitudes
def target_altitudes(target: dict[str, Any], times: list[datetime], site: Site) -> list[float]:
    location = EarthLocation(lat=site.lat * u.deg, lon=site.lon * u.deg, height=site.elevation_m * u.m)
    coord = SkyCoord(float(target["ra_deg"]) * u.deg, float(target["dec_deg"]) * u.deg, frame="icrs")
    frame = AltAz(obstime=Time(times), location=location)
    return [float(value) for value in coord.transform_to(frame).alt.deg]


# Function: best_visible_time
def best_visible_time(
    target: dict[str, Any],
    times: list[datetime],
    site: Site,
    min_alt_deg: float,
) -> tuple[datetime, float] | None:
    alts = target_altitudes(target, times, site)
    visible = [(dt, alt) for dt, alt in zip(times, alts, strict=True) if alt >= min_alt_deg]
    if not visible:
        return None
    return max(visible, key=lambda row: row[1])


# Function: target_due
def target_due(target: dict[str, Any], ledger: dict[str, Any], plan_date: date) -> tuple[bool, str]:
    if not ledger:
        return True, "no_ledger"
    entry = ledger.get(str(target.get("name"))) or {}
    last_success = entry.get("last_success_utc")
    cadence_days = float(target.get("cadence_days", 1.0))
    if not last_success:
        return True, "new_or_unsuccessful"
    age = datetime.combine(plan_date, datetime.min.time(), tzinfo=timezone.utc) - parse_utc(last_success)
    if age >= timedelta(days=cadence_days):
        return True, "cadence_due"
    return False, "cadence_not_due"


# Function: build_nightly_plan
def build_nightly_plan(
    objects_path: Path,
    site_path: Path,
    weather_path: Path,
    out_dir: Path,
    ledger_path: Path | None = None,
    start_utc: str | None = None,
    end_utc: str | None = None,
    min_alt_deg: float = 30.0,
    sun_alt_limit: float = -12.0,
    max_targets: int = 25,
) -> dict[str, Any]:
    proof = StateLedger(out_dir)
    object_payload = load_json(objects_path)
    objects = list(object_payload.get("targets", object_payload) if isinstance(object_payload, dict) else object_payload)
    site = parse_site(load_json(site_path))
    weather_ok, weather_reason = weather_allows(load_json(weather_path) if weather_path.exists() else {})
    proof.record("weather", "pass" if weather_ok else "fail", evidence=str(weather_path), reason=weather_reason)
    if not weather_ok:
        return {"targets": [], "metadata": {"weather": weather_reason}}

    now = datetime.now(timezone.utc)
    start = parse_utc(start_utc) if start_utc else now
    end = parse_utc(end_utc) if end_utc else start + timedelta(hours=12)
    dark = dark_times(time_grid(start, end), site, sun_alt_limit)
    proof.record("dark_window", "pass" if dark else "fail", extra={"samples": len(dark)})
    if not dark:
        return {"targets": [], "metadata": {"weather": weather_reason, "dark_samples": 0}}

    ledger = load_json(ledger_path) if ledger_path and ledger_path.exists() else {}
    planned = []
    for target in objects:
        due, due_reason = target_due(target, ledger, start.date())
        if not due:
            proof.record("cadence", "skip", target=target.get("name"), reason=due_reason)
            continue
        best = best_visible_time(target, dark, site, min_alt_deg)
        if best is None:
            proof.record("visibility", "skip", target=target.get("name"), reason="not_visible")
            continue
        best_dt, best_alt = best
        planned.append(
            {
                "name": target["name"],
                "ra_deg": float(target["ra_deg"]),
                "dec_deg": float(target["dec_deg"]),
                "best_start_utc": best_dt.isoformat().replace("+00:00", "Z"),
                "max_alt_deg": round(best_alt, 2),
                "integration_sec": int(target.get("integration_sec", 600)),
                "priority": int(target.get("priority", 100)),
            }
        )
        proof.record("visibility", "pass", target=target["name"], extra={"max_alt_deg": round(best_alt, 2)})

    planned = sorted(planned, key=lambda row: (row["priority"], row["best_start_utc"]))[:max_targets]
    for index, target in enumerate(planned, start=1):
        target["recommended_order"] = index

    output = {
        "#objective": "Seevar-Lite nightly AAVSO preflight plan.",
        "metadata": {
            "weather": weather_reason,
            "dark_samples": len(dark),
            "min_alt_deg": min_alt_deg,
            "sun_alt_limit": sun_alt_limit,
        },
        "targets": planned,
    }
    out_path = out_dir / "nightly_plan.json"
    out_path.write_text(json.dumps(output, indent=2, sort_keys=True), encoding="utf-8")
    proof.record("plan", "pass", evidence=str(out_path), extra={"target_count": len(planned)})
    return output
