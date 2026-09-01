# Changelog

This project follows semantic versioning. User-visible changes are recorded
here before a release.

## [Unreleased]

### Added

- Open-source project governance and contribution documentation.
- Automated Windows quality checks and tagged release builds.
- Dependency update automation and reproducible direct-dependency constraints.
- Fast source development launcher with controlled restart on Python changes.
- No-audio, no-model indicator preview mode.
- Stable per-user model cache shared by later and preview builds.
- Identifiable Windows preview artifacts for every pull request.
- Versioned, validated settings storage with migration and atomic writes.
- Separate normal and development settings locations with privacy-safe recovery
  warnings.
- Accessible PySide6 system tray, settings window, and non-activating status
  overlay using native Windows scaling and colours.
- Multi-display overlay placement tests and a real-Windows interface acceptance
  checklist.
- PySide6 and Qt notices in preview and release archives.
- Live Automatic, English, Norwegian, and Multilingual language selection.
- Live Windows microphone selection with disconnected-device recovery.
- Validated push-to-talk capture for Right Ctrl and F6 through F12,
  including safe listener replacement and Restore Default.
- Curated multilingual Tiny, Base, Small, and Medium model manager with pinned
  revisions, checksums, hardware guidance, atomic installation, removal, and
  verified folder import.
- Background local model switching with persistence rollback and no executable
  rebuild requirement.
- Per-model byte and percentage progress for downloading and verification, with
  safe cancellation that preserves installed and active models.

### Fixed

- Wait for a newly captured push-to-talk key to be released before restarting
  the global listener, preventing hotkey changes from leaving dictation stuck.
- Recognise the extended Windows scan code Qt reports for Right Ctrl while
  keeping Alt and the left-side modifier keys unavailable.

## [0.1.0] - 2026-08-31

### Added

- Hold Right Ctrl to record from the Windows default microphone.
- Local multilingual faster-whisper transcription on CPU.
- Automatic language detection, including English and Norwegian.
- Direct Unicode insertion without using the clipboard.
- Floating recording and transcription status indicator.
- In-memory audio handling with no transcript or audio history.
- Portable PyInstaller build script for Windows and Python 3.14.
