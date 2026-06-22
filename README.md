# CapFrameX Sync Start

Start your CapFrameX capture at the **same point in every benchmark run** — just
before the first rocket is fired in your demo — so your results are directly
comparable, even though the demo takes a different amount of time to load each
time.

## The idea

The only thing that varies between runs is the **load time**. Once the demo is
actually *playing*, the first rocket is fired at a fixed point in demo time
(~13 s in). So instead of timing from when you press play, this tool:

1. **Watches the screen for the loading screen to end** (gameplay appears).
   That's the stable anchor — it ignores however long loading took.
2. **Waits the fixed in-demo offset** to the rocket, minus a small lead, so the
   capture starts *just before* the shot.
3. **Sends your CapFrameX capture hotkey.**
4. **CapFrameX captures for a fixed Capture Time** and auto-stops. The tool
   prints the exact number to set (`demo length − offset` ≈ **179 s** for a
   3:12 demo with a 13 s offset).

## Setup (one time)

1. **Install Python 3** — https://www.python.org/ (tick "Add Python to PATH").
2. **Install the dependencies** — open a terminal in this folder and run:
   ```
   pip install -r requirements.txt
   ```
3. **In CapFrameX** (Settings):
   - Set a **Capture Hotkey** (e.g. `F11`).
   - Set **Capture Time** to the number the tool prints (~`179 s`), so every
     capture runs from the rocket to the end of the demo and stops itself.
4. **Edit the CONFIG block** at the top of `sync_capture.py`:
   - `CAPTURE_HOTKEY` — match the CapFrameX hotkey (e.g. `"f11"`).
   - `ROCKET_OFFSET_S` — you'll measure this next (`--calibrate`).
   - `DEMO_LENGTH_S` — your demo length in seconds (3:12 = `192`).

> On Windows, open the terminal **as administrator** so the keyboard library is
> allowed to send the hotkey to the game/CapFrameX.

## Measure your rocket offset (once)

```
python sync_capture.py --calibrate
```

1. Start your demo. When the **loading screen** is visible, press **Enter** to
   arm (the tool grabs a reference of the loading screen).
2. The tool automatically detects when **gameplay** appears and starts a timer.
3. Press **Enter** the instant the **first rocket** fires.
4. It prints your measured `ROCKET_OFFSET_S` and the CapFrameX `Capture Time`.

Run it two or three times and average. Put the result in `ROCKET_OFFSET_S`.

## Run a synced capture (every test)

```
python sync_capture.py
```

1. Start your demo. When the **loading screen** is visible, press **Enter** to
   arm.
2. The tool watches for gameplay, then waits your offset and fires the capture
   hotkey just before the rocket. CapFrameX records for the fixed Capture Time
   and stops itself.

Because the anchor is the *end of loading*, the capture begins at the identical
point in the demo every run — regardless of how long loading took.

## If detection misfires (`--tune`)

If your loading screen has an animation (spinner, progress bar) that trips the
detector early, tune the threshold:

```
python sync_capture.py --tune
```

Arm at the loading screen; the tool prints a live `diff` value. It should read
**low** on the loading screen and **jump high** when gameplay appears. Pick a
`DIFF_THRESHOLD` between the two values and set it in the CONFIG block.

You can also restrict detection to a specific area by setting `REGION` to
`(left, top, width, height)` — useful to avoid an animated loading element.

## Config reference (top of `sync_capture.py`)

| Setting | Meaning |
| --- | --- |
| `CAPTURE_HOTKEY` | CapFrameX capture hotkey, e.g. `"f11"`, `"ctrl+f11"` |
| `ROCKET_OFFSET_S` | Seconds from gameplay start to the first rocket (~13) |
| `LEAD_S` | Start the capture this many seconds before the rocket |
| `DEMO_LENGTH_S` | Total demo length in seconds (3:12 = 192) |
| `REGION` | `None` for full screen, or `(left, top, width, height)` |
| `DIFF_THRESHOLD` | Difference above which loading is considered over |
| `STABLE_FRAMES` | Consecutive frames needed to confirm the change |

## Troubleshooting

- **Hotkey doesn't reach the game/CapFrameX** — run the terminal as
  administrator. CapFrameX's hotkey is a global OS hook, so it's caught even
  when the game is focused.
- **Capture starts too early/late** — re-run `--calibrate` a few times and
  average; adjust `LEAD_S` to nudge the start earlier/later.
- **Detector triggers during loading** — use `--tune` to raise `DIFF_THRESHOLD`,
  and/or set `REGION` to an area that's clearly different between the loading
  screen and gameplay.
