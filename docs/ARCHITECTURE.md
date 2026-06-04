# Architecture

Seevar-Lite is deliberately small.

Preflight:

```text
object JSON
-> weather gate
-> dark-window gate
-> altitude visibility gate
-> cadence gate
-> nightly_plan.json
-> JSON proof/state
```

Postflight:

```text
FITS frames
-> group by OBJECT
-> median stack
-> require WCS
-> aperture photometry
-> AAVSO Extended report
-> JSON proof/state
```

Hard rules:
- no WCS means no photometry
- no comparison ensemble means no report
- no accepted photometry means no AAVSO row
- every step writes proof JSON

Future execution layer:

```text
SeeVar planner
-> seestarpy or seestar_alp plan
-> Seestar native solve/track/stack
-> Seevar-Lite postflight
```

The telescope should do telescope work. Seevar-Lite should prove and report the science.
