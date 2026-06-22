# CapFrameX Sync Start

Start **and stop** your CapFrameX capture at the same point in every benchmark
run — just before the first rocket is fired in your Rust demo — so your results
are directly comparable, even though the demo takes a different amount of time to
load each time. **Fully hands-off: no keypress during a run.**

## The idea

The only thing that varies between runs is the **load time**. Once the demo is
actually *playing*, the first rocket is fired at a fixed point in demo time. The
Rust loading screen is **static**; the moment it ends there's a huge one-frame
change on screen. So this tool:

1. **Detects when the loading screen ends** (the big change), and confirms the
   demo is now playing. That moment is the stable anchor — it ignores however
   long loading took.
2. **Waits the fixed offset** to the rocket, minus a small lead, so the capture
   starts *just before* the shot.
3. **Sends your CapFrameX capture hotkey to start.**
4. **Sends it again after the computed duration** (the demo's end) to stop.

## Measured from your reference video

These are baked into the defaults in `sync_capture.py`:

| What | Value | How it was measured |
| --- | --- | --- |
| Loading screen | static, change ≈ 0.01 | flat for the whole load |
| Loading **ends** | one-frame change ≈ **108** | brightness jumps 86 → 187 |
| Loading ended at | 22.92 s | first big change after the static load |
| Rocket launch flash | 37.20 s | red flash + smoke from the circled building |
| **Rocket offset** | **≈ 14.3 s** | 37.20 − 22.92 (after loading ends) |
| Demo length | 192 s (3:12) | given |
| **Capture duration** | **≈ 178 s** | 192 − (14.3 − 0.3 lead) |

In-game motion during the demo is very low (~0.1), which is why the tool
triggers on the **loading-end transition**, not on motion.

## Setup (one time)

1. **Install Python 3** — https://www.python.org/ (tick "Add Python to PATH").
2. **Install the dependencies** — open a terminal in this folder and run:
   ```
   pip install -r requirements.txt
   ```
3. **In CapFrameX** (Settings):
   - Set a **Capture Hotkey** (e.g. `F11`), and set `CAPTURE_HOTKEY` to match.
   - Set **Capture Time** to **0 / manual** so the hotkey can both start and
     stop (the script sends it twice). *Or* leave Capture Time at ~`178 s` and
     set `STOP_HOTKEY = None` in the script to let CapFrameX stop itself.
4. The measured values above are already set, but you can confirm
   `ROCKET_OFFSET_S` with `--calibrate`.

> On Windows, open the terminal **as administrator** so the keyboard library is
> allowed to send the hotkey to the game/CapFrameX.

## Run a synced capture (every test) — hands-off

```
python sync_capture.py
```

Then just **start your demo**. The tool watches the screen, detects when loading
ends, waits ~14 s, fires the capture hotkey just before the rocket, then stops it
~178 s later at the end of the demo. No input from you.

Because the anchor is the *end of loading*, the capture begins at the identical
point in the demo every run — regardless of how long loading took.

## Re-measure the offset (`--calibrate`)

If you ever want to re-check the 14.3 s offset:

```
python sync_capture.py --calibrate
```

Start your demo; the tool auto-detects when loading ends, then you press **Enter**
the instant the rocket fires. It prints the measured `ROCKET_OFFSET_S` and the
capture duration. Run it a couple of times and average.

## If detection misfires (`--tune`)

```
python sync_capture.py --tune
```

Start your demo and watch the live `change` value. The loading screen should read
**~0**; the instant loading ends should **spike high** (≈100); gameplay then
reads low but non-zero. The defaults (`STATIC_THRESHOLD 3`,
`TRANSITION_THRESHOLD 15`) sit cleanly between those, but adjust if your system
differs. If a loading animation keeps the screen from being static, set `REGION`
to a calmer area.

## Config reference (top of `sync_capture.py`)

| Setting | Meaning |
| --- | --- |
| `CAPTURE_HOTKEY` | CapFrameX capture hotkey, e.g. `"f11"` |
| `STOP_HOTKEY` | Key to stop; same as capture (toggle), or `None` for CapFrameX Capture Time |
| `ROCKET_OFFSET_S` | Seconds from loading-end to the rocket (≈14.3) |
| `LEAD_S` | Start the capture this many seconds before the rocket |
| `DEMO_LENGTH_S` | Total demo length in seconds (3:12 = 192) |
| `CAPTURE_DURATION_S` | `None` = auto (demo end), or a fixed number of seconds |
| `REGION` | `None` for full screen, or `(left, top, width, height)` |
| `TRANSITION_THRESHOLD` | Change above which loading is considered over |
| `STATIC_THRESHOLD` | Change below which the screen counts as static (loading) |

## Troubleshooting

- **Hotkey doesn't reach the game/CapFrameX** — run the terminal as
  administrator. CapFrameX's hotkey is a global OS hook, so it's caught even
  when the game is focused.
- **Capture doesn't stop** — your CapFrameX is auto-stopping on its Capture Time
  before the second hotkey, or the hotkey isn't a toggle. Set CapFrameX Capture
  Time to 0, or set `STOP_HOTKEY = None` and use CapFrameX's Capture Time (~178 s).
- **Triggers too early** — a static screen (e.g. desktop) preceded loading; the
  tool already guards against this by confirming the demo is "alive" after the
  change. If it still fires early, raise `TRANSITION_THRESHOLD` via `--tune`.
- **Capture is slightly off the rocket** — re-run `--calibrate` and average;
  nudge `LEAD_S` to move the start earlier/later.
