"""
CapFrameX Sync Start
====================

Starts your CapFrameX capture at the same point in every benchmark run, even
though the demo takes a different amount of time to load each time.

How it works
------------
The only thing that varies between runs is the load time. Once the demo is
actually *playing*, the first rocket is fired at a fixed point in demo time
(~13 s in). So this script:

  1. Watches the screen for the loading screen to END (gameplay appears).
     That is the stable anchor -- it ignores however long loading took.
  2. Waits the fixed in-demo offset to the rocket, minus a small lead, so the
     capture starts just BEFORE the shot.
  3. Sends your CapFrameX capture hotkey.
  4. CapFrameX captures for a fixed "Capture Time" (which it auto-stops). The
     script prints the exact number to set for that (demo length - offset).

Usage
-----
  python sync_capture.py            Run a synchronized capture
  python sync_capture.py --calibrate  Measure your rocket offset (~13 s)
  python sync_capture.py --tune       Show live detection values to set the
                                       threshold for your loading screen

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

# Seconds from the moment gameplay starts (loading ends) to the first rocket.
# Measure this once with:  python sync_capture.py --calibrate
ROCKET_OFFSET_S = 13.0

# Start the capture this many seconds BEFORE the rocket (a small safety lead).
LEAD_S = 0.3

# Total demo length in seconds. 3:12 = 192 s. Used only to print the CapFrameX
# "Capture Time" you should set (so the capture runs to the end of the demo).
DEMO_LENGTH_S = 192.0

# Screen region to watch, as (left, top, width, height) in pixels.
# Use None for the whole primary monitor (works well for loading -> gameplay).
REGION = None

# --- Detection tuning (defaults are sensible; adjust with --tune if needed) ---
# Average pixel-difference (0-255) above which the screen is "no longer the
# loading screen". Raise it if a loading animation causes false triggers.
DIFF_THRESHOLD = 25.0
# How many consecutive frames must exceed the threshold to confirm the change.
STABLE_FRAMES = 5
# Downscale factor for speed (every Nth pixel). Higher = faster, less precise.
DOWNSCALE_STEP = 4

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


def capture_baseline(sct, region, frames=10):
    """Average a few frames of the (static) loading screen as the baseline."""
    acc = None
    for _ in range(frames):
        g = grab_gray(sct, region)
        acc = g if acc is None else acc + g
        time.sleep(0.01)
    return acc / frames


def wait_for_loading_to_end(sct, region, baseline):
    """Block until gameplay appears; return the time the change first began."""
    consecutive = 0
    first_exceed_t = None
    while True:
        g = grab_gray(sct, region)
        diff = float(np.abs(g - baseline).mean())
        if diff > DIFF_THRESHOLD:
            if consecutive == 0:
                first_exceed_t = time.perf_counter()   # start of the change
            consecutive += 1
            if consecutive >= STABLE_FRAMES:
                return first_exceed_t
        else:
            consecutive = 0
            first_exceed_t = None
        time.sleep(0.002)


def arm(sct, region):
    """Prompt the user to arm at the loading screen and grab the baseline."""
    input("\n>> Start your demo. When the LOADING SCREEN is visible, "
          "press Enter here to arm... ")
    print("   Capturing loading-screen reference...")
    baseline = capture_baseline(sct, region)
    print("   Armed. Watching for gameplay to appear...")
    return baseline


def fire_capture():
    keyboard.send(CAPTURE_HOTKEY)


def run():
    start_offset = ROCKET_OFFSET_S - LEAD_S
    capture_time = DEMO_LENGTH_S - start_offset
    print(__doc__.split("Usage")[0].rstrip())
    print(f"\n  Capture hotkey      : {CAPTURE_HOTKEY}")
    print(f"  Rocket offset       : {ROCKET_OFFSET_S:.2f} s "
          f"(start {LEAD_S:.2f} s early)")
    print(f"  >> Set CapFrameX 'Capture Time' to: {capture_time:.1f} s\n")

    with mss.mss() as sct:
        region = get_region(sct)
        baseline = arm(sct, region)
        t0 = wait_for_loading_to_end(sct, region, baseline)
        print(f"   Gameplay detected! Rocket in ~{start_offset:.2f} s...")

        fire_at = t0 + start_offset
        while time.perf_counter() < fire_at:
            time.sleep(0.001)
        fire_capture()
        print(f"   >> CAPTURE STARTED (rocket). Running ~{capture_time:.0f} s.")


def calibrate():
    """Detect load-end, then time how long until you say the rocket fired."""
    print("CALIBRATION: we'll detect when gameplay starts, then you press "
          "Enter the moment the first rocket fires.\n")
    with mss.mss() as sct:
        region = get_region(sct)
        baseline = arm(sct, region)
        t0 = wait_for_loading_to_end(sct, region, baseline)
        print("   Gameplay detected! Watch closely...")
        input("   >> Press Enter the INSTANT the first rocket fires. ")
        offset = time.perf_counter() - t0
        cap = DEMO_LENGTH_S - (offset - LEAD_S)
        print(f"\n   Measured rocket offset: {offset:.2f} s")
        print(f"   Set in config:  ROCKET_OFFSET_S = {offset:.2f}")
        print(f"   CapFrameX Capture Time:  {cap:.1f} s")
        print("   (Run a few times and average for the tightest sync.)")


def tune():
    """Print live diff values so you can pick DIFF_THRESHOLD for your screen."""
    print("TUNE: showing live difference from the loading-screen baseline.\n"
          "Loading screen should read LOW; gameplay should jump HIGH.\n"
          "Pick a DIFF_THRESHOLD between the two. Ctrl+C to stop.\n")
    with mss.mss() as sct:
        region = get_region(sct)
        baseline = arm(sct, region)
        try:
            while True:
                g = grab_gray(sct, region)
                diff = float(np.abs(g - baseline).mean())
                bar = "#" * min(int(diff), 60)
                print(f"\rdiff={diff:6.1f} | {bar:<60}", end="")
                time.sleep(0.05)
        except KeyboardInterrupt:
            print("\nDone.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CapFrameX Sync Start")
    parser.add_argument("--calibrate", action="store_true",
                        help="measure your rocket offset")
    parser.add_argument("--tune", action="store_true",
                        help="show live detection values")
    args = parser.parse_args()

    if args.calibrate:
        calibrate()
    elif args.tune:
        tune()
    else:
        run()
