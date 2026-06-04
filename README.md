# Seevar-Lite

Clean AAVSO-first reducer for SeeVar.

Scope:
- build a nightly AAVSO plan from object/weather/dark-window JSON
- ingest FITS frames
- stack by target
- require WCS proof
- perform aperture photometry from JSON catalogs
- write state/proof JSON
- stage AAVSO Extended report rows

Not in scope:
- telescope steering
- dashboard
- direct Alpaca exposure loops
- pretty-picture processing

## Quick Start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'

seevar-lite-postflight \
  --frames /path/to/fits \
  --targets examples/targets.json \
  --comparisons examples/comparisons.json \
  --out runs/test
```

Preflight:

```bash
seevar-lite-preflight \
  --objects catalogs/campaign_targets.json \
  --site examples/site.json \
  --weather examples/weather.json \
  --out runs/preflight \
  --start-utc 2026-06-04T20:00:00Z \
  --end-utc 2026-06-05T03:00:00Z
```

Outputs:
- `runs/preflight/nightly_plan.json`
- `runs/test/state.json`
- `runs/test/proof.jsonl`
- `runs/test/stacks/*.fits`
- `runs/test/reports/aavso_extended.txt`

## JSON Catalogs

Targets use the existing SeeVar campaign catalog shape:

```json
{
  "targets": [
    {
      "name": "ST Boo",
      "ra": 224.44,
      "dec": 40.73,
      "recommended_cadence_days": 1,
      "duration": 600
    }
  ]
}
```

Comparison stars:

```json
{
  "ST Boo": [
    {"id": "C1", "ra_deg": 224.41, "dec_deg": 40.71, "mag": 12.3},
    {"id": "C2", "ra_deg": 224.48, "dec_deg": 40.76, "mag": 12.8}
  ]
}
```

The first rule is simple: no WCS, no photometry, no AAVSO row.
