## CapFrame Sync Start v1.0.0

Hands-off synchronized CapFrameX capture for the Rust benchmark demo. Starts —
and stops — every capture at the identical point in the demo (just before the
first rocket), regardless of how long the demo takes to load.

### How it works
- Detects the **loading-screen-end transition** on screen (robust to variable
  load time) and confirms the demo is playing, so a desktop→loading flash can't
  false-trigger.
- Waits the fixed in-demo offset and fires the **CapFrameX capture hotkey** just
  before the rocket, then stops it at the demo's end.

### Measured from the reference demo
- Loading ends at ~22.92 s → first rocket flash at 37.20 s
- **Rocket offset ≈ 14.3 s** after loading ends
- **Capture duration ≈ 178 s** (3:12 demo − ~14 s)

### Included
- `sync_capture.py` — hands-off run, plus `--calibrate` (re-measure offset) and
  `--tune` (verify detection thresholds)
- `requirements.txt`, `README.md`

### Setup
1. `pip install -r requirements.txt`
2. Set the CapFrameX capture hotkey (match `CAPTURE_HOTKEY`); set Capture Time to
   0 so the script can toggle stop.
3. Run `python sync_capture.py`, then start your demo. Done.
