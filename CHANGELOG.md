# Changelog

This project follows semantic versioning. User-visible changes are recorded
here before a release.

## [Unreleased]

## [0.2.0-alpha.2] - 2026-09-02

### Changed

- Redesign the settings window around a calmer, more deliberate visual
  hierarchy with compact status, dictation, application, model, privacy, and
  product-information sections.
- Keep Save and Cancel available while settings content scrolls on smaller
  laptop displays.
- Show language-specific guidance and provide direct navigation from the
  current model to model management.
- Present only the model actions that are relevant to the selected model, with
  a separate path for importing a verified model from another computer.
- Expand the Privacy and About pages with plain-language explanations of local
  processing, storage boundaries, offline use, and Skrivi's non-generative
  purpose.
- Use a warm Skrivi theme with stronger control boundaries, visible keyboard
  focus, clear disabled states, palette-aware dark styling, and Windows
  high-contrast fallback.
- Complete the redesigned interface in English and Norwegian Bokmål while
  continuing to label English as English in language pickers.

### Fixed

- Avoid repeating Skrivi's product name in the Windows settings title bar.
- Prevent long build labels and model-status messages from clipping.

## [0.2.0-alpha.1] - 2026-09-02

### Added

- Rename the product from Bragi to Skrivi across the Windows application,
  executable, website, documentation, build artifacts, and package metadata.
- Automatically move existing Bragi settings and downloaded models into
  Skrivi's application-data directories without copying model weights or
  requiring another download.
- Continue recognising existing Bragi model exports while replacing their
  manifest filename with the Skrivi name after local verification.
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
- Retry failed startup model loading from the tray, the dictation key, or after
  activating a model in Settings without restarting Skrivi.
- Coordinated shutdown that stops input, cancels model operations, prevents late
  text insertion, and waits briefly for in-memory cleanup.
- Complete Norwegian Bokmål interface for the tray, settings, status messages,
  model manager, errors, guidance, and accessibility labels, with automatic
  Windows-language selection and an explicit language setting.
- Live English and Norwegian interface previews that update existing controls,
  tray actions, overlay messages, model progress, and accessibility labels,
  with Cancel restoring the saved language.
- Per-user Windows installer with Start menu, optional desktop shortcut,
  standard uninstall support, and no administrator requirement.
- Default-off automatic startup setting for packaged builds, backed by an
  isolated Windows platform service and safe persistence rollback.

### Fixed

- Keep every letter in the website wordmark at one consistent size and enlarge
  the tray icon with light-and-dark taskbar contrast.
- Return to Ready after a transcription failure, discard the recording, and
  allow the next dictation to proceed without restarting.
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
