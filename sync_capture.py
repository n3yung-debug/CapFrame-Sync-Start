"""
CapFrameX Sync Start
====================

Starts (and stops) your CapFrameX capture at the same point in every benchmark
run, even though the demo takes a different amount of time to load each time.
Fully hands-off: no keypress during a run.

Tuned from the reference recording of this Rust demo
----------------------------------------------------
  * The loading screen is perfectly STATIC (frame-to-frame change ~0.01).
  * When loading ends there is a huge ONE-FRAME change (change jumps to ~108,
    brightness 86 -> 187). That transition is the stable anchor.
  * In-game motion afterwards is very LOW (~0.1), so we trigger on the
    transition, not on sustained motion.
  * Loading screen ended at 22.92 s; the first rocket's launch flash was at
    37.20 s  ->  ROCKET_OFFSET_S = ~14.3 s after loading ends.
  * Demo length 3:12 (192 s)  ->  capture runs ~178 s (192 - ~14).

How it works
------------
  1. Watch the screen. Wait for a sustained STATIC stretch (the loading screen),
     then the first big change (loading ends). Confirm the scene is now "alive"
     (the demo is playing) so a desktop->loading change can't false-trigger.
  2. Wait the fixed offset to the rocket, minus a small lead, so the capture
     starts just BEFORE the shot.
  3. Send the CapFrameX capture hotkey to START.
  4. After the computed duration (demo end), send the hotkey again to STOP.

Usage
-----
  python sync_capture.py              Run a synchronized capture (hands-off)
  python sync_capture.py --calibrate  Re-measure the rocket offset
  python sync_capture.py --tune       Show live change values for detection

Requirements:  pip install -r requirements.txt   (mss, numpy, keyboard)
On Windows, run from a terminal opened "as administrator" so the keyboard
library can send the hotkey to the game/CapFrameX.
"""

import argparse
import time

import numpy as np
import mss
import keyboard


# ============================== CONFIG =======================================

# CapFrameX capture hotkey. Must match CapFrameX > Settings > Capture Hotkey.
# Examples: "f11", "f12", "ctrl+f11", "shift+f12".
CAPTURE_HOTKEY = "f11"

# Hotkey to STOP the capture. With CapFrameX's "Capture Time" set to 0 (manual),
# the capture hotkey toggles, so the same key stops it. Set to None to let
# CapFrameX's own Capture Time stop the capture instead.
STOP_HOTKEY = "f11"

# Seconds from the moment the loading screen ends to the first rocket.
# Measured from the reference video: 37.20 - 22.92 = 14.28 s.
ROCKET_OFFSET_S = 14.3

# Start the capture this many seconds BEFORE the rocket (a small safety lead).
LEAD_S = 0.3

# Total demo length in seconds. 3:12 = 192 s.
DEMO_LENGTH_S = 192.0

# How long the capture should run. None = auto (DEMO_LENGTH - where we start),
# i.e. from just before the rocket to the end of the demo (~178 s here).
CAPTURE_DURATION_S = None

# Screen region to watch, as (left, top, width, height). None = whole monitor.
REGION = None

# --- Detection tuning (measured defaults; verify with --tune) -----------------
# Frame-to-frame "change" is the average pixel difference (0-255) between frames.
STATIC_THRESHOLD = 3.0      # below this = a static screen (loading). Measured ~0.01
TRANSITION_THRESHOLD = 15.0  # above this = loading ended. Measured spike ~108
STATIC_SECONDS = 1.0        # how long it must stay static to count as loading
ALIVE_WINDOW_S = 1.0        # window after the change used to confirm gameplay
ALIVE_THRESHOLD = 0.04      # avg change over that window that means "playing"
DOWNSCALE_STEP = 4          # speed: compare every Nth pixel

# =============================================================================


def get_region(sct):
    """Return the mss region dict to capture (REGION or the primary monitor)."""
    if REGION is None:
        return sct.monitors[1]
    left, top, width, height = REGION
    return {"left": left, "top": top, "width": width, "height": height}


def grab_gray(sct, region):
    """Grab the region as a small grayscale array for fast comparison."""
    raw = np.asarray(sct.grab(region))           # H x W x 4 (BGRA)
    small = raw[::DOWNSCALE_STEP, ::DOWNSCALE_STEP, :3]
    return small.mean(axis=2)                      # grayscale


def wait_static(sct, region, prev):
    """Block until the screen has been static for STATIC_SECONDS. Return frame."""
    static_since = None
    while True:
        time.sleep(0.002)
        cur = grab_gray(sct, region)
        change = float(np.abs(cur - prev).mean())
        prev = cur
        now = time.perf_counter()
        if change < STATIC_THRESHOLD:
            static_since = static_since or now
            if now - static_since >= STATIC_SECONDS:
                return prev
        else:
            static_since = None


def wait_transition(sct, region, prev):
    """Block until a big one-frame change. Return (time, frame)."""
    while True:
        time.sleep(0.002)
        cur = grab_gray(sct, region)
        change = float(np.abs(cur - prev).mean())
        prev = cur
        if change > TRANSITION_THRESHOLD:
            return time.perf_counter(), prev


def scene_is_alive(sct, region, prev):
    """After a change, confirm the scene keeps moving (the demo is playing),
    so a desktop->loading change can't be mistaken for the demo starting."""
    end = time.perf_counter() + ALIVE_WINDOW_S
    total = 0.0
    count = 0
    while time.perf_counter() < end:
        time.sleep(0.005)
        cur = grab_gray(sct, region)
        total += float(np.abs(cur - prev).mean())
        prev = cur
        count += 1
    return count > 0 and (total / count) > ALIVE_THRESHOLD


def wait_for_load_end(sct, region):
    """Return the time the loading screen ended (the demo's first frame)."""
    prev = grab_gray(sct, region)
    while True:
        prev = wait_static(sct, region, prev)        # the loading screen
        t_change, prev = wait_transition(sct, region, prev)   # loading ends
        if scene_is_alive(sct, region, prev):        # confirm it's the demo
            return t_change
        # Otherwise it was e.g. desktop -> loading; keep waiting.


def sleep_until(t):
    while True:
        d = t - time.perf_counter()
        if d <= 0:
            return
        time.sleep(min(0.005, d))


def run():
    start_offset = max(0.0, ROCKET_OFFSET_S - LEAD_S)
    duration = (CAPTURE_DURATION_S if CAPTURE_DURATION_S is not None
                else DEMO_LENGTH_S - start_offset)
    print(__doc__.split("Usage")[0].rstrip())
    print(f"\n  Capture hotkey   : {CAPTURE_HOTKEY}")
    print(f"  Rocket offset    : {ROCKET_OFFSET_S:.2f} s after loading ends "
          f"(start {LEAD_S:.2f} s early)")
    print(f"  Capture duration : {duration:.1f} s")
    print(f"  Stop             : "
          f"{'script sends ' + STOP_HOTKEY if STOP_HOTKEY else 'CapFrameX Capture Time'}\n")

    with mss.mss() as sct:
        region = get_region(sct)
        print(">> Start your demo now. Watching for the loading screen "
              "to end...")
        t0 = wait_for_load_end(sct, region)
        print(f"   Loading ended. Capture fires in ~{start_offset:.1f} s "
              "(just before the rocket)...")

        sleep_until(t0 + start_offset)
        keyboard.send(CAPTURE_HOTKEY)
        print("   >> CAPTURE STARTED (rocket).")

        if STOP_HOTKEY:
            stop_at = time.perf_counter() + duration
            while True:
                rem = stop_at - time.perf_counter()
                if rem <= 0:
                    break
                print(f"\r   capturing... {rem:5.1f} s left ", end="")
                time.sleep(min(0.2, rem))
            keyboard.send(STOP_HOTKEY)
            print("\n   >> CAPTURE STOPPED.")
        else:
            print(f"   CapFrameX will stop after its Capture Time "
                  f"(set it to {duration:.1f} s).")


def calibrate():
    """Auto-detect load-end, then time how long until you mark the rocket."""
    print("CALIBRATION: start your demo. The tool auto-detects when loading "
          "ends, then you press Enter the moment the first rocket fires.\n")
    with mss.mss() as sct:
        region = get_region(sct)
        print(">> Start your demo now. Watching for the loading screen "
              "to end...")
        t0 = wait_for_load_end(sct, region)
        print("   Loading ended! Watch closely...")
        input("   >> Press Enter the INSTANT the first rocket fires. ")
        offset = time.perf_counter() - t0
        cap = DEMO_LENGTH_S - (offset - LEAD_S)
        print(f"\n   Measured rocket offset: {offset:.2f} s")
        print(f"   Set in config:  ROCKET_OFFSET_S = {offset:.2f}")
        print(f"   Capture duration:  {cap:.1f} s")
        print("   (Run a few times and average for the tightest sync.)")


def tune():
    """Print live change values so you can verify the detection thresholds."""
    print("TUNE: showing live frame-to-frame change.\n"
          "Loading screen should read ~0; the moment loading ends should\n"
          "spike well above TRANSITION_THRESHOLD; gameplay then reads low but\n"
          "non-zero. Ctrl+C to stop.\n")
    with mss.mss() as sct:
        region = get_region(sct)
        prev = grab_gray(sct, region)
        peak = 0.0
        try:
            while True:
                time.sleep(0.02)
                cur = grab_gray(sct, region)
                change = float(np.abs(cur - prev).mean())
                prev = cur
                peak = max(peak, change)
                bar = "#" * min(int(change), 60)
                print(f"\rchange={change:6.2f}  peak={peak:6.1f} | {bar:<60}",
                      end="")
        except KeyboardInterrupt:
            print("\nDone.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CapFrameX Sync Start")
    parser.add_argument("--calibrate", action="store_true",
                        help="measure your rocket offset")
    parser.add_argument("--tune", action="store_true",
                        help="show live change values")
    args = parser.parse_args()

    if args.calibrate:
        calibrate()
    elif args.tune:
        tune()
    else:
        run()
