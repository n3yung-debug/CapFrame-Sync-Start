"""
CapFrameX Sync Start
====================

Starts (and stops) your CapFrameX capture at the same point in every benchmark
run, even though the demo takes a different amount of time to load each time.

Two-part activation
--------------------
  1. Run the script. It waits, doing nothing.
  2. Get your demo to the LOADING SCREEN, then press the ARM hotkey (default F8).
     The script snapshots the loading screen and starts watching for it to end.

This avoids false triggers: detection only begins once you arm it on the
loading screen, and it fires the instant the screen changes away from that
loading screen (i.e. the demo actually starts).

Tuned from the reference recording of this Rust demo
----------------------------------------------------
  * The loading screen is static; the moment it ends the whole screen changes.
  * Loading ended at 22.92 s; the first rocket's launch flash was at 37.20 s
    ->  ROCKET_OFFSET_S = ~14.3 s after loading ends.
  * Demo length 3:12 (192 s)  ->  capture runs ~178 s (192 - ~14).

How it works
------------
  1. You press ARM on the loading screen -> snapshot it as the baseline.
  2. Watch for the screen to differ from that baseline and stay different
     (the demo started). That moment is the load-end anchor.
  3. Wait the fixed offset to the rocket, minus a small lead, then send the
     CapFrameX capture hotkey to START.
  4. After the computed duration (demo end), send the hotkey again to STOP.

Usage
-----
  python sync_capture.py              Run a synchronized capture
  python sync_capture.py --calibrate  Re-measure the rocket offset
  python sync_capture.py --tune       Show live difference from the baseline

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

# Hotkey you press, while the LOADING SCREEN is visible, to arm detection.
ARM_HOTKEY = "f8"

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

# --- Detection tuning (verify with --tune) -----------------------------------
# After arming, the loading screen reads ~0 difference from the snapshot; when
# the demo starts the difference jumps well above this. Measured jump is large.
DIVERGENCE_THRESHOLD = 20.0   # difference above which the loading screen is gone
DIVERGENCE_CONFIRM_S = 0.3    # difference must persist this long to confirm
BASELINE_FRAMES = 10          # frames averaged when snapshotting the loading screen
DOWNSCALE_STEP = 4            # speed: compare every Nth pixel

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


def snapshot_baseline(sct, region):
    """Average a few frames of the current (loading) screen as the baseline."""
    acc = None
    for _ in range(BASELINE_FRAMES):
        g = grab_gray(sct, region)
        acc = g if acc is None else acc + g
        time.sleep(0.01)
    return acc / BASELINE_FRAMES


def arm(label="start detection"):
    """Block until the user presses the ARM hotkey on the loading screen."""
    print(f"\n>> Get the demo to the LOADING SCREEN, then press "
          f"'{ARM_HOTKEY.upper()}' to {label}.")
    keyboard.wait(ARM_HOTKEY)


def wait_for_load_end(sct, region):
    """After arming, return the time the screen left the loading screen."""
    baseline = snapshot_baseline(sct, region)
    print("   Armed on the loading screen. Waiting for the demo to start...")
    diverged_since = None
    while True:
        time.sleep(0.002)
        cur = grab_gray(sct, region)
        diff = float(np.abs(cur - baseline).mean())
        now = time.perf_counter()
        if diff > DIVERGENCE_THRESHOLD:
            if diverged_since is None:
                diverged_since = now          # first frame off the loading screen
            if now - diverged_since >= DIVERGENCE_CONFIRM_S:
                return diverged_since
        else:
            diverged_since = None


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
    print(f"\n  Arm hotkey       : {ARM_HOTKEY}")
    print(f"  Capture hotkey   : {CAPTURE_HOTKEY}")
    print(f"  Rocket offset    : {ROCKET_OFFSET_S:.2f} s after loading ends "
          f"(start {LEAD_S:.2f} s early)")
    print(f"  Capture duration : {duration:.1f} s")
    print(f"  Stop             : "
          f"{'script sends ' + STOP_HOTKEY if STOP_HOTKEY else 'CapFrameX Capture Time'}")

    with mss.mss() as sct:
        region = get_region(sct)
        arm()
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
    """Arm on the loading screen, then time how long until you mark the rocket."""
    print("CALIBRATION: arm on the loading screen; the tool detects when it "
          "ends, then you press Enter the moment the first rocket fires.")
    with mss.mss() as sct:
        region = get_region(sct)
        arm()
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
    """Arm on the loading screen, then show live difference from the snapshot."""
    print("TUNE: arm on the loading screen, then watch the live difference.\n"
          "It should read ~0 while the loading screen is up, and jump well\n"
          "above DIVERGENCE_THRESHOLD the instant the demo starts. Ctrl+C to stop.")
    with mss.mss() as sct:
        region = get_region(sct)
        arm("snapshot the loading screen")
        baseline = snapshot_baseline(sct, region)
        peak = 0.0
        try:
            while True:
                time.sleep(0.02)
                cur = grab_gray(sct, region)
                diff = float(np.abs(cur - baseline).mean())
                peak = max(peak, diff)
                bar = "#" * min(int(diff), 60)
                print(f"\rdiff={diff:6.2f}  peak={peak:6.1f} | {bar:<60}", end="")
        except KeyboardInterrupt:
            print("\nDone.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CapFrameX Sync Start")
    parser.add_argument("--calibrate", action="store_true",
                        help="measure your rocket offset")
    parser.add_argument("--tune", action="store_true",
                        help="show live difference from the loading-screen snapshot")
    args = parser.parse_args()

    if args.calibrate:
        calibrate()
    elif args.tune:
        tune()
    else:
        run()
