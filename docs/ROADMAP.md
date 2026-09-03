# Roadmap

The project has a long-term assistive-technology ambition, but releases progress
through evidence-based quality gates. See [QUALITY_BAR.md](QUALITY_BAR.md). The
current priority is a trustworthy personal desktop application.

## v0.2: configurable desktop application

- Replace the prototype settings experience with a PySide6 settings window.
- Keep the compact no-focus recording overlay.
- Add a validated, versioned settings file.
- Add a curated model selector with download sizes and CPU guidance.
- Show model download and loading progress.
- Verify pinned model files before atomic installation.
- Allow microphone and hotkey selection.
- Support Automatic, Norwegian, and English language modes, with Automatic
  restricted to Norwegian and English detection.
- Offer the complete interface in English and Norwegian Bokmål, following the
  Windows display language initially with an explicit language choice in Settings.
- Add start-with-Windows and overlay appearance settings.
- Provide a conventional per-user Windows installer while retaining the
  portable ZIP.
- Preserve the no-audio-history and no-transcript-history defaults.

### Acceptance criteria

- Settings survive restart and recover safely from invalid configuration.
- Model changes do not require rebuilding the executable.
- Slow models display a hardware suitability warning before download.
- No settings operation blocks recording or the UI event loop.
- Existing push-to-talk behaviour remains covered by automated tests.
- A tagged commit produces a downloadable Windows release automatically.

## v0.3: reliability and distribution

- Resumable downloads and reclaiming unused model-cache files.
- Microphone reconnection and clearer error recovery.
- Installer upgrade and managed-deployment improvements informed by alpha
  testing.
- Optional non-content diagnostic logs with redaction tests.
- Code signing when a sustainable certificate strategy is available.
- Software bill of materials and automated vulnerability scanning.
- Keyboard-only, high-contrast and screen-reader verification.
- A repeatable English and Norwegian accuracy benchmark.

## Later candidates

- Spoken formatting commands as an explicit non-verbatim mode.
- GPU acceleration where compatible hardware is detected.
- Additional operating systems after the Windows experience is stable.
- Opt-in update notifications.
