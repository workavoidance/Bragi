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

## [0.1.0] - 2026-08-31

### Added

- Hold Right Ctrl to record from the Windows default microphone.
- Local multilingual faster-whisper transcription on CPU.
- Automatic language detection, including English and Norwegian.
- Direct Unicode insertion without using the clipboard.
- Floating recording and transcription status indicator.
- In-memory audio handling with no transcript or audio history.
- Portable PyInstaller build script for Windows and Python 3.14.
