# CapFrameX Sync Start

Start your CapFrameX capture at the **exact same point in every benchmark run** —
the moment the first rocket is fired in your demo — so your results are directly
comparable across tests.

## The idea

In a recorded demo, the first rocket is fired at a fixed time after the demo
starts. CapFrameX begins a capture when it receives its **global capture
hotkey**. So all we need is to press that hotkey at the same instant every run.

`sync_capture.ahk` does exactly that: it waits a measured offset
(`RocketDelayMs`) from a reference point, then sends your CapFrameX capture
hotkey for you. Identical timing, every time — no human reaction-time error.

## Setup (one time)

1. **Install AutoHotkey v2** — https://www.autohotkey.com/ (pick v2.0).
2. **In CapFrameX** (Settings):
   - Set a **Capture Hotkey** (e.g. `F11`) and note it.
   - Recommended: set a fixed **Capture Time** (e.g. 30 s) so each capture
     auto-stops after the same duration. That keeps every run the same length.
3. **Edit `sync_capture.ahk`** and set the three values at the top:
   - `CaptureHotkey` — must match the CapFrameX capture hotkey from step 2.
   - `RocketDelayMs` — your rocket offset (you'll measure this next).
   - `DemoStartKey` — optional, see "Two ways to sync" below.
4. **Run it** — double-click `sync_capture.ahk`. A green **H** icon appears in
   the system tray, meaning it's listening for the hotkeys.

## Measure your rocket offset (F7)

Do this once so the script knows how long to wait:

1. Press **F7** at your reference point (the instant the demo starts playing).
2. Watch the demo. Press **F7** again the moment you **see** the first rocket.
3. The elapsed milliseconds appear on screen and are copied to your clipboard.
4. Paste that number into `RocketDelayMs` in `sync_capture.ahk`, then press
   **F9** to reload the script.

Do it two or three times and average the results for the tightest sync.

## Run a synced capture (F8)

Each test run, just press **F8** at your reference point. The script waits your
`RocketDelayMs` and then fires the capture hotkey precisely on the rocket. Every
run starts the capture at the identical point in the demo.

## Two ways to sync

- **Manual reference (default, `DemoStartKey := ""`)** — start the demo yourself
  and press **F8** at that instant. Simple; as long as you measured the offset
  the same way, your runs line up.
- **Locked reference (`DemoStartKey := "{Enter}"`, etc.)** — put the key that
  starts your demo into `DemoStartKey`. Then **F8** both starts the demo *and*
  the timer, so they're locked together for frame-perfect sync. Use this if your
  game accepts the keystroke.

## Hotkey reference

| Key | Action |
| --- | --- |
| F8  | Run a synchronized capture |
| F7  | Calibration stopwatch (measure the rocket offset) |
| F9  | Reload the script after editing the config |
| F10 | Quit the script |

## Troubleshooting

- **The capture hotkey doesn't fire the game/CapFrameX.** If your game runs as
  administrator, run AutoHotkey as administrator too (right-click the `.ahk` →
  Run as administrator), otherwise Windows blocks synthesized keys from reaching
  an elevated window. CapFrameX's hotkey is a global OS hook, so it usually
  catches the keypress even when the game is focused.
- **`DemoStartKey` doesn't start the demo.** Some games ignore synthesized
  keystrokes (DirectInput). In that case leave `DemoStartKey := ""` and start the
  demo manually, pressing **F8** at that instant.
- **Sync drifts a little.** Re-measure with F7 a few times and average. Make sure
  you press F8 at the same reference point you measured from.
