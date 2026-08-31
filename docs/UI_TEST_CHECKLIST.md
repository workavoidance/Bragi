# Windows interface acceptance checklist

Use this checklist on the portable pull-request build before merging a major
interface change. Record the Windows version, display arrangement, scaling,
theme, keyboard used, and result in the pull request.

## Core workflow

- Start Bragi and confirm the tray status changes from loading to ready without
  freezing its menu.
- Hold Right Ctrl, speak, release it, and confirm the text is inserted exactly
  as before the interface change.
- Confirm recording and transcription continue while the Settings window is
  open.
- Exit from the tray during idle, then repeat during recording.

## Keyboard and assistive access

- Open the tray menu from the Windows notification area using only the
  keyboard, then open Settings and exit Bragi.
- In Settings, use Tab, Shift+Tab, arrow keys, Alt+G, Alt+P, Alt+A, Ctrl+S and
  Escape. Confirm every action has a visible focus indicator.
- With Windows Narrator, confirm the window, tabs, overlay option, Save, Cancel,
  status text, and any settings warning have useful names.
- Confirm loading, ready, listening, transcribing, no-speech and error states
  are understandable without relying on colour.

## Display and theme matrix

- Test Windows text scaling at 100%, 150% and 200%. Confirm no text is clipped.
- Test Windows high-contrast mode and both normal light and dark application
  themes. Confirm text, focus and disabled controls remain legible.
- Test two displays with different scaling. Put the pointer on each display,
  dictate, and confirm the overlay stays inside that display's work area.
- Repeat with the second display positioned left of and above the primary
  display, covering negative desktop coordinates.
- Open Settings on each display and confirm its size and controls scale cleanly.

## Privacy and offline behaviour

- Confirm preview mode does not request microphone access or load a model.
- After the model is installed, disconnect the network, restart Windows, and
  confirm normal dictation, Settings and the tray still work.
- Confirm no recording, transcript or dictated text appears in the settings
  file or application directory.
