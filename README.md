# CapFrameX Sync Start

Start **and stop** your CapFrameX capture at the same point in every benchmark
run — just before the first rocket is fired in your Rust demo — so your results
are directly comparable, even though the demo takes a different amount of time to
load each time.

## The idea

The only thing that varies between runs is the **load time**. Once the demo is
actually *playing*, the first rocket is fired at a fixed point in demo time. So
this tool uses a **two-part activation**:

1. **Run the script** — it waits, doing nothing.
2. **Press the ARM hotkey (default `F8`) while the loading screen is showing** —
   the tool snapshots the loading screen and starts watching for it to end.
3. **The instant the screen changes away from the loading screen** (the demo
   starts), that's the anchor — it ignores however long loading took.
4. **Waits the fixed offset** to the rocket, minus a small lead, then **sends
   your CapFrameX capture hotkey to start**, and **again after the computed
   duration** (the demo's end) to stop.

Arming on the loading screen is what makes detection reliable: it can't be
fooled by desktop/menu activity before the demo, because it only compares
against the loading screen you armed on.

## Measured from your reference video

These are baked into the defaults in `sync_capture.py`:

| What | Value | How it was measured |
| --- | --- | --- |
| Loading screen | static | flat for the whole load |
| Loading **ends** | whole screen changes | brightness jumps 86 → 187 |
| Loading ended at | 22.92 s | first big change after the static load |
| Rocket launch flash | 37.20 s | red flash + smoke from the circled building |
| **Rocket offset** | **≈ 14.3 s** | 37.20 − 22.92 (after loading ends) |
| Demo length | 192 s (3:12) | given |
| **Capture duration** | **≈ 178 s** | 192 − (14.3 − 0.3 lead) |

The whole screen changes when loading ends, so the tool fires on that change
relative to the loading screen you armed on.

## Setup (one time)

1. **Install Python 3** — https://www.python.org/ (tick "Add Python to PATH").
2. **Install the dependencies** — open a terminal in this folder and run:
   ```
   pip install -r requirements.txt
   ```
3. **In CapFrameX** (Settings):
   - Note your **Capture Hotkey** — the default in this script is `[` (set
     `CAPTURE_HOTKEY` / `STOP_HOTKEY` to match yours).
   - Set **Capture Time** to **0 / manual** so the hotkey can both start and
     stop (the script sends it twice). *Or* leave Capture Time at ~`178 s` and
     set `STOP_HOTKEY = None` in the script to let CapFrameX stop itself.
4. Pick an **`ARM_HOTKEY`** (default `F8`) — a key you'll press on the loading
   screen (must be different from the capture key).
5. **Verify detection on your machine (required first run)** — see the next
   section. This is the most important step: it confirms the tool can actually
   tell when *your* demo's loading screen ends, and sets the right threshold.

> On Windows, open the terminal **as administrator** so the keyboard library is
> allowed to send the hotkey to the game/CapFrameX.

## Step 1 — Verify detection (`--tune`), do this first

```
python sync_capture.py --tune
```

1. Start your demo. When the **loading screen** appears, press **`F8`**.
2. Stay on the loading screen for ~1.5 s while it measures.
3. Let the demo start. The tool reports:
   - how steady the loading screen read (should be low),
   - how big the jump was when the demo started, and
   - a **RESULT** (reliable / marginal) plus a **recommended
     `DIVERGENCE_THRESHOLD`**.

If it says *Good separation*, you're set — update `DIVERGENCE_THRESHOLD` to the
recommended value if it differs. If *Marginal*, set `REGION` to a steadier part
of the screen (away from overlays/animations) and run it again. Then re-run once
more to confirm it catches the load-end cleanly before relying on it.

## Step 2 — Run a synced capture (every test)

```
python sync_capture.py
```

1. Start your demo. When the **loading screen** appears, press **`F8`** (the ARM
   hotkey). The tool snapshots the loading screen.
2. The instant the demo starts (screen changes), the tool waits ~14 s and fires
   the capture hotkey just before the rocket, then stops it ~178 s later at the
   end of the demo.

Because the anchor is the *end of loading*, the capture begins at the identical
point in the demo every run — regardless of how long loading took. Arming on the
loading screen means desktop/menu activity before the demo can't trigger it.

## Re-measure the offset (`--calibrate`)

If you ever want to re-check the 14.3 s offset:

```
python sync_capture.py --calibrate
```

Press **`F8`** on the loading screen; the tool detects when it ends, then you
press **Enter** the instant the rocket fires. It prints the measured
`ROCKET_OFFSET_S` and the capture duration. Run it a couple of times and average.

## Config reference (top of `sync_capture.py`)

| Setting | Meaning |
| --- | --- |
| `CAPTURE_HOTKEY` | CapFrameX capture hotkey, e.g. `"f11"` |
| `STOP_HOTKEY` | Key to stop; same as capture (toggle), or `None` for CapFrameX Capture Time |
| `ARM_HOTKEY` | Key you press on the loading screen to begin detection (`"f8"`) |
| `ROCKET_OFFSET_S` | Seconds from loading-end to the rocket (≈14.3) |
| `LEAD_S` | Start the capture this many seconds before the rocket |
| `DEMO_LENGTH_S` | Total demo length in seconds (3:12 = 192) |
| `CAPTURE_DURATION_S` | `None` = auto (demo end), or a fixed number of seconds |
| `REGION` | `None` for full screen, or `(left, top, width, height)` |
| `DIVERGENCE_THRESHOLD` | Difference from the loading-screen snapshot that means it ended |
| `DIVERGENCE_CONFIRM_S` | How long that difference must persist to confirm |

## Troubleshooting

- **Hotkey doesn't reach the game/CapFrameX** — run the terminal as
  administrator. CapFrameX's hotkey is a global OS hook, so it's caught even
  when the game is focused.
- **Capture doesn't stop** — your CapFrameX is auto-stopping on its Capture Time
  before the second hotkey, or the hotkey isn't a toggle. Set CapFrameX Capture
  Time to 0, or set `STOP_HOTKEY = None` and use CapFrameX's Capture Time (~178 s).
- **Fires instantly / too early** — make sure you press `F8` *while the loading
  screen is showing*, not before. If it still fires early, raise
  `DIVERGENCE_THRESHOLD` via `--tune`.
- **Capture is slightly off the rocket** — re-run `--calibrate` and average;
  nudge `LEAD_S` to move the start earlier/later.
