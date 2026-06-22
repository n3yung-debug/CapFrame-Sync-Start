"""
CapFrameX Sync Start
====================

Starts your CapFrameX capture at the same point in every benchmark run, even
though the demo takes a different amount of time to load each time. Fully
hands-off: no keypress during a run.

How it works
------------
The only thing that varies between runs is the load time. Once the demo is
actually *playing*, the first rocket is fired at a fixed point in demo time
(~13 s in). The loading screen is static (no motion); gameplay has continuous
motion. So this script:

  1. Watches the screen and waits for a STATIC stretch (the loading screen)
     followed by sustained MOTION -- that onset of motion is gameplay starting,
     i.e. the moment loading ends. It ignores however long loading took.
  2. Waits the fixed in-demo offset to the rocket, minus a small lead, so the
     capture starts just BEFORE the shot.
  3. Sends your CapFrameX capture hotkey.
  4. CapFrameX captures for a fixed "Capture Time" (which it auto-stops). The
     script prints the exact number to set for that (demo length - offset).

Usage
-----
  python sync_capture.py              Run a synchronized capture (hands-off)
  python sync_capture.py --calibrate  Measure your rocket offset (~13 s)
  python sync_capture.py --tune       Show live motion values to set the
                                       thresholds for your demo

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

# --- Detection tuning (defaults are sensible; check/adjust with --tune) -------
# Frame-to-frame "motion" is the average pixel change (0-255) between frames.
# Loading screen ~ near 0; gameplay ~ clearly higher.
MOTION_THRESHOLD = 8.0     # motion above this counts as gameplay
STATIC_THRESHOLD = 3.0     # motion below this counts as a static (loading) frame
STATIC_SECONDS = 0.5       # how long it must stay static to qualify as loading
MOTION_CONFIRM_SECONDS = 0.12  # how long motion must persist to confirm gameplay
DOWNSCALE_STEP = 4         # speed: compare every Nth pixel

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


def wait_for_gameplay(sct, region):
    """Block until gameplay starts; return the time motion first began.

    Waits for a sustained static stretch (the loading screen), then for
    sustained motion (gameplay). The first frame of that motion is the
    load-end anchor.
    """
    prev = grab_gray(sct, region)
    seen_static = False
    static_since = None
    motion_since = None
    while True:
        time.sleep(0.002)
        cur = grab_gray(sct, region)
        motion = float(np.abs(cur - prev).mean())
        prev = cur
        now = time.perf_counter()

        if not seen_static:
            # First, confirm we're on a static screen (the loading screen).
            if motion < STATIC_THRESHOLD:
                static_since = static_since or now
                if now - static_since >= STATIC_SECONDS:
                    seen_static = True
            else:
                static_since = None
        else:
            # Then, wait for sustained motion -> gameplay has started.
            if motion > MOTION_THRESHOLD:
                motion_since = motion_since or now
                if now - motion_since >= MOTION_CONFIRM_SECONDS:
                    return motion_since          # onset of gameplay motion
            else:
                motion_since = None


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
        print(">> Start your demo now. Watching for the loading screen "
              "to end...")
        t0 = wait_for_gameplay(sct, region)
        print(f"   Gameplay detected! Rocket in ~{start_offset:.2f} s...")

        fire_at = t0 + start_offset
        while time.perf_counter() < fire_at:
            time.sleep(0.001)
        fire_capture()
        print(f"   >> CAPTURE STARTED (rocket). Running ~{capture_time:.0f} s.")


def calibrate():
    """Auto-detect load-end, then time how long until you mark the rocket."""
    print("CALIBRATION: start your demo. The tool auto-detects when gameplay "
          "begins, then you press Enter the moment the first rocket fires.\n")
    with mss.mss() as sct:
        region = get_region(sct)
        print(">> Start your demo now. Watching for the loading screen "
              "to end...")
        t0 = wait_for_gameplay(sct, region)
        print("   Gameplay detected! Watch closely...")
        input("   >> Press Enter the INSTANT the first rocket fires. ")
        offset = time.perf_counter() - t0
        cap = DEMO_LENGTH_S - (offset - LEAD_S)
        print(f"\n   Measured rocket offset: {offset:.2f} s")
        print(f"   Set in config:  ROCKET_OFFSET_S = {offset:.2f}")
        print(f"   CapFrameX Capture Time:  {cap:.1f} s")
        print("   (Run a few times and average for the tightest sync.)")


def tune():
    """Print live motion values so you can set the detection thresholds."""
    print("TUNE: showing live frame-to-frame motion.\n"
          "Loading screen should read LOW (near 0); gameplay should read HIGH.\n"
          "Set STATIC_THRESHOLD just above the loading value and "
          "MOTION_THRESHOLD just below the gameplay value. Ctrl+C to stop.\n")
    with mss.mss() as sct:
        region = get_region(sct)
        prev = grab_gray(sct, region)
        try:
            while True:
                time.sleep(0.05)
                cur = grab_gray(sct, region)
                motion = float(np.abs(cur - prev).mean())
                prev = cur
                bar = "#" * min(int(motion), 60)
                print(f"\rmotion={motion:6.1f} | {bar:<60}", end="")
        except KeyboardInterrupt:
            print("\nDone.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CapFrameX Sync Start")
    parser.add_argument("--calibrate", action="store_true",
                        help="measure your rocket offset")
    parser.add_argument("--tune", action="store_true",
                        help="show live motion values")
    args = parser.parse_args()

    if args.calibrate:
        calibrate()
    elif args.tune:
        tune()
    else:
        run()
