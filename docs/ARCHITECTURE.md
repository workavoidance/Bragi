# Architecture

Bragi is a Windows tray application with a privacy-first local speech pipeline.

## Current flow

1. A global Right Ctrl listener starts in-memory microphone capture.
2. Releasing Right Ctrl closes the audio stream.
3. Audio is normalised to mono 16 kHz float32 data.
4. faster-whisper detects the language and transcribes locally.
5. Windows `SendInput` inserts UTF-16 text at the existing cursor.
6. Audio buffers are overwritten on a best-effort basis and references are
   released.

The clipboard is not used.

## Target module boundaries

- `core`: state machine, capture orchestration and transcription workflow.
- `models`: supported model catalogue, downloads, validation and removal.
- `settings`: versioned configuration, defaults and migration.
- `platform`: Windows hotkeys, Unicode insertion, startup and device discovery.
- `ui`: tray icon, recording overlay, settings window and error presentation.

The core must not import the user-interface implementation. UI events cross the
boundary through small interfaces so core behaviour remains independently
testable.

## Threading

Audio callbacks, model loading and transcription must never block the UI event
loop. Only one transcription is accepted at a time until a deliberate queuing
policy is introduced.

## Data ownership

Models and configuration are persistent. Recordings and transcripts are not.
Diagnostic logs may contain state transitions, durations, model names and error
types, but never dictated content or raw audio.

Downloaded models live in `%LOCALAPPDATA%\Bragi\models` and are shared across
normal, development, and preview builds. Future development settings use a
separate `%APPDATA%\Bragi\development` location. Initial setup and explicit model
downloads may use the internet; installed transcription remains local and must
continue working without it.

The UI-independent settings module accepts and emits an explicit versioned
schema. It validates a strict field allowlist, migrates old schemas in memory,
returns privacy-safe recovery warnings, and replaces settings files atomically.
Invalid and newer-version files are preserved for diagnosis or recovery.
