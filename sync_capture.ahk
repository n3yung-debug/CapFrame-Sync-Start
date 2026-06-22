#Requires AutoHotkey v2.0
#SingleInstance Force

; =============================================================================
;  CapFrameX Sync Start
;  Fires the CapFrameX capture hotkey at the EXACT same moment in every run,
;  so all of your benchmark captures begin on the first rocket shot.
;
;  HOW IT WORKS
;    The rocket is fired at a fixed time after the demo starts. This script
;    waits that exact offset (RocketDelayMs) from a reference point and then
;    sends your CapFrameX capture hotkey. Same timing, every time.
;
;  QUICK START
;    1. Install AutoHotkey v2:  https://www.autohotkey.com/
;    2. In CapFrameX, set your capture hotkey and (recommended) a fixed
;       "Capture Time" so the capture auto-stops after N seconds.
;    3. Set the three CONFIG values below.
;    4. Double-click this file to run it (a green "H" appears in the tray).
;    5. Calibrate once with F7 (see CALIBRATION), then use F8 each run.
;
;  HOTKEYS
;    F8  -> Run a synchronized capture (start reference -> wait -> fire capture)
;    F7  -> Calibration stopwatch (measure your rocket offset, see below)
;    F9  -> Reload this script after editing the config
;    F10 -> Quit this script
; =============================================================================


; ============================== CONFIG =======================================

; Your CapFrameX capture hotkey. Must match CapFrameX > Settings > Capture Hotkey.
; Examples: "{F11}", "{F12}", "^{F11}" (Ctrl+F11), "+{F12}" (Shift+F12).
global CaptureHotkey := "{F11}"

; Measured time (in milliseconds) from the reference point to the first rocket.
; Measure this ONCE with the F7 calibration stopwatch, then paste the number here.
global RocketDelayMs := 7300

; OPTIONAL: a key the script will press to START the demo, so the timer and the
; demo are locked together for frame-perfect sync. Leave as "" to start the demo
; yourself and press F8 at that instant. Example: "{Enter}" or "p".
global DemoStartKey := ""

; =============================================================================


; ------------------------------ F8: RUN --------------------------------------
F8:: {
    ; If configured, kick off the demo so timing is locked to it.
    if (DemoStartKey != "")
        Send(DemoStartKey)

    ToolTip("Synced run started - capture will fire in " RocketDelayMs " ms")
    Sleep(RocketDelayMs)

    Send(CaptureHotkey)
    ToolTip("CAPTURE TRIGGERED (rocket shot)")
    SetTimer(() => ToolTip(), -2000)
}


; --------------------------- F7: CALIBRATION ---------------------------------
; Measure your rocket offset:
;   1. Press F7 at your reference point (the instant the demo starts).
;   2. Watch the demo. Press F7 again the moment you SEE the first rocket fire.
;   3. The elapsed milliseconds are shown and copied to your clipboard.
;   4. Paste that number into RocketDelayMs above and press F9 to reload.
; Repeat a couple of times and average for best accuracy.
global CalStart := 0
F7:: {
    global CalStart
    if (CalStart = 0) {
        CalStart := A_TickCount
        ToolTip("Stopwatch STARTED - press F7 again the instant the rocket fires")
    } else {
        elapsed := A_TickCount - CalStart
        CalStart := 0
        A_Clipboard := elapsed
        ToolTip("Rocket at " elapsed " ms  (copied to clipboard)`n"
              . "Set:  global RocketDelayMs := " elapsed)
        SetTimer(() => ToolTip(), -8000)
    }
}


; ------------------------ F9 / F10: RELOAD & QUIT ----------------------------
F9::Reload()
F10::ExitApp()
