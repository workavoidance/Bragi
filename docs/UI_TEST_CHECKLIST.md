# Windows interface acceptance checklist

Use this checklist on the portable pull-request build before merging a major
interface change. Record the Windows version, display arrangement, scaling,
theme, keyboard used, and result in the pull request.

## Deferred manual QA

This manual interface pass was deferred on 2026-09-01 so issue #6 development
could continue. Nothing below is considered complete by deferral. Run and
record the full checklist before the v0.2 release candidate, and before closing
issue #8.

## Core workflow

- Start Bragi and confirm the tray status changes from loading to ready without
  freezing its menu.
- Hold Right Ctrl, speak, release it, and confirm the text is inserted exactly
  as before the interface change.
- Confirm recording and transcription continue while the Settings window is
  open.
- Exit from the tray during idle, then repeat during recording.
- In Settings, change the language between Automatic, English, Norwegian, and
  Multilingual. Confirm the next recording uses the new choice without a restart.
- Select an available microphone, save, and dictate without restarting. Then
  disconnect it and confirm the next dictation temporarily uses Windows Default.
  Reconnect it and confirm Bragi automatically returns to the selection.
- With Windows Default selected, change the default input in Windows Sound
  settings and confirm the next dictation uses the new default without restarting.
- Disconnect a microphone during a recording and confirm that recording is
  discarded, Bragi returns to Ready, and the next dictation can start normally.
- Change the push-to-talk key, confirm the old key no longer records, and confirm
  the new key records exactly once per press. Restore Right Ctrl afterward.
- Dictate Norwegian text containing `æ`, `ø`, and `å` after each configuration
  change and confirm direct insertion is still correct.
- Open Models and confirm Tiny, Base, Small, and Medium show download size, RAM
  guidance, CPU suitability, and clear installed or not-installed state.
- Download Base, watch download, verification, and loading feedback, activate
  it, and dictate without restarting Bragi. Confirm Small can then be restored.
- Interrupt a non-default model download by exiting Bragi. Restart and confirm
  the partial model is not offered as installed and can be downloaded again.
- Copy an installed non-active model folder to another location, remove it in
  Bragi, import the copied folder, and confirm it passes verification.
- Disconnect the network, restart Windows, switch between two installed models,
  and dictate successfully with both.

## Keyboard and assistive access

- Open the tray menu from the Windows notification area using only the
  keyboard, then open Settings and exit Bragi.
- In Settings, use Tab, Shift+Tab, arrow keys, Alt+G, Alt+P, Alt+A, Ctrl+S and
  Escape. Confirm every action has a visible focus indicator.
- With Windows Narrator, confirm the window, tabs, overlay option, Save, Cancel,
  language, microphone, hotkey controls, status text, and any settings warning
  have useful names.
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
