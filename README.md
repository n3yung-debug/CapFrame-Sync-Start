# CapFrameX Sync Start

Start your CapFrameX capture at the **same point in every benchmark run** — just
before the first rocket is fired in your demo — so your results are directly
comparable, even though the demo takes a different amount of time to load each
time. **Fully hands-off: no keypress during a run.**

## The idea

The only thing that varies between runs is the **load time**. Once the demo is
actually *playing*, the first rocket is fired at a fixed point in demo time
(~13 s in). The loading screen is **static** (no motion); gameplay has
**continuous motion**. So instead of timing from when you press play, this tool:

1. **Detects when the loading screen ends** — it waits for a static stretch (the
   loading screen) followed by sustained motion (gameplay). That onset of motion
   is the stable anchor, and it ignores however long loading took.
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

1. Run the command, then **start your demo**.
2. The tool automatically detects when **gameplay** begins and starts a timer.
3. Press **Enter** the instant the **first rocket** fires.
4. It prints your measured `ROCKET_OFFSET_S` and the CapFrameX `Capture Time`.

Run it two or three times and average. Put the result in `ROCKET_OFFSET_S`.
(This is the only step that needs a keypress, and only during setup.)

## Run a synced capture (every test) — hands-off

```
python sync_capture.py
```

Then just **start your demo**. The tool watches the screen, detects when loading
ends, waits your offset, and fires the capture hotkey just before the rocket —
no input from you. CapFrameX records for the fixed Capture Time and stops itself.

Because the anchor is the *end of loading*, the capture begins at the identical
point in the demo every run — regardless of how long loading took.

## If detection misfires (`--tune`)

If the trigger comes early or late, check your motion values:

```
python sync_capture.py --tune
```

Start your demo and watch the live `motion` number. It should read **low (near
0)** on the loading screen and **jump high** during gameplay. Then in the CONFIG
block set:

- `STATIC_THRESHOLD` just **above** the loading-screen value, and
- `MOTION_THRESHOLD` just **below** the gameplay value.

If a loading animation (spinner, progress bar, background video) keeps the motion
high, set `REGION` to `(left, top, width, height)` to watch a calmer area of the
screen instead of the whole monitor.

## Config reference (top of `sync_capture.py`)

| Setting | Meaning |
| --- | --- |
| `CAPTURE_HOTKEY` | CapFrameX capture hotkey, e.g. `"f11"`, `"ctrl+f11"` |
| `ROCKET_OFFSET_S` | Seconds from gameplay start to the first rocket (~13) |
| `LEAD_S` | Start the capture this many seconds before the rocket |
| `DEMO_LENGTH_S` | Total demo length in seconds (3:12 = 192) |
| `REGION` | `None` for full screen, or `(left, top, width, height)` |
| `MOTION_THRESHOLD` | Motion above this counts as gameplay |
| `STATIC_THRESHOLD` | Motion below this counts as the static loading screen |
| `STATIC_SECONDS` | How long it must stay static to qualify as loading |
| `MOTION_CONFIRM_SECONDS` | How long motion must persist to confirm gameplay |

## Troubleshooting

- **Hotkey doesn't reach the game/CapFrameX** — run the terminal as
  administrator. CapFrameX's hotkey is a global OS hook, so it's caught even
  when the game is focused.
- **Triggers too early (during loading)** — your loading screen isn't fully
  static. Use `--tune` to raise `MOTION_THRESHOLD`, or set `REGION` to a calmer
  area.
- **Triggers late / not at all** — gameplay motion is below `MOTION_THRESHOLD`;
  lower it using `--tune`.
- **Capture starts slightly early/late vs the rocket** — re-run `--calibrate`
  and average; nudge `LEAD_S` to move the start earlier/later.
