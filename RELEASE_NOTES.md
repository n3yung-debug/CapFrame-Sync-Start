## CapFrame Sync Start v1.0.2

### Fixed
- **`--calibrate` now registers the rocket mark.** It previously waited for
  Enter via the terminal, which only works when the terminal is focused — so
  pressing Enter during the demo (with the game focused) did nothing. Calibration
  now uses a global hotkey: press **`F8`** (`MARK_HOTKEY`) the instant the rocket
  fires, caught even while the game is focused. A short debounce ignores the
  arming keypress.

### Setup
1. `pip install -r requirements.txt`
2. Set the CapFrameX capture hotkey to match `CAPTURE_HOTKEY` (`[`); set Capture
   Time to 0 so the script can toggle stop.
3. **Verify detection:** `python sync_capture.py --tune` (arm on the loading
   screen with `F8`, let the demo start, follow the RESULT).
4. **Measure offset (optional):** `python sync_capture.py --calibrate` — press
   `F8` on the loading screen, then `F8` again when the rocket fires.
5. Run `python sync_capture.py`, press `F8` on the loading screen, done.
