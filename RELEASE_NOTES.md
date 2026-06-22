## CapFrame Sync Start v1.0.1

Reliability fixes for triggering and a required detection-check step.

### Changed
- **Two-part activation** — run the script, then press the **ARM hotkey
  (`F8`) while the loading screen is showing**. This fixes the previous
  instant/false triggering (the old auto-detector could fire on desktop/menu
  activity before the demo even loaded).
- **Baseline-divergence detection** — arming snapshots the loading screen, and
  the capture fires the instant the screen changes away from it (the demo
  starting). More reliable than the earlier motion heuristic.
- **Capture hotkey default is now `[`** (`CAPTURE_HOTKEY` / `STOP_HOTKEY`).
- **`--tune` is now a guided pass/fail detection check** — it measures the
  loading-screen reading and the jump when the demo starts, then reports a
  RESULT and a recommended `DIVERGENCE_THRESHOLD`. Documented as the required
  first step before your first real capture.

### Unchanged (from the reference demo)
- Rocket offset ≈ 14.3 s after loading ends; capture duration ≈ 178 s.

### Setup
1. `pip install -r requirements.txt`
2. Set the CapFrameX capture hotkey to match `CAPTURE_HOTKEY` (`[`); set Capture
   Time to 0 so the script can toggle stop.
3. **Verify detection:** `python sync_capture.py --tune` (arm on the loading
   screen with `F8`, let the demo start, follow the RESULT).
4. Run `python sync_capture.py`, press `F8` on the loading screen, done.
