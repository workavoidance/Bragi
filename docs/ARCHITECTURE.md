# Architecture

**Language:** [Norsk](ARCHITECTURE_NB.md) | English

Skrivi is a Windows tray application with a privacy-first local speech pipeline.

## Current flow

1. A configurable global push-to-talk listener starts in-memory microphone
   capture. Right Ctrl is the default.
2. Releasing the configured key closes the audio stream.
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

Downloaded models live in `%LOCALAPPDATA%\Skrivi\models` and are shared across
normal, development, and preview builds. Future development settings use a
separate `%APPDATA%\Skrivi\development` location. Initial setup and explicit model
downloads may use the internet; installed transcription remains local and must
continue working without it.

The Skrivi rename migrates the previous Bragi application-data roots with an
atomic same-volume directory rename. A failed rename falls back to the existing
directory so settings and large model downloads are never abandoned merely
because the branding changed. Legacy model manifests remain readable and are
renamed after validation.

The model catalogue is compiled into Skrivi with immutable upstream revisions,
file sizes, and checksums. Downloads and imports are verified in a staging
directory before an atomic install. The transcriber receives an installed local
path rather than a remote model identifier, preventing an accidental network
lookup during normal dictation. Candidate models load before the active model is
swapped, and settings failures restore the previous in-memory model.

If the startup model cannot load, the controller enters a recoverable error
state. Only one background retry can run at a time. The tray, dictation key, and
a successful model activation can request that retry. A transcription failure
discards the current in-memory audio and returns the controller to Ready so the
next dictation can proceed without restarting the process.

Application exit uses one bounded shutdown sequence. It hides the tray, blocks
new controller and model work, stops the global listener and microphone, signals
transcription and model cancellation, then waits up to five seconds for workers
to clear in-memory audio and remove incomplete staging files. The single-instance
lock is released last, including when a cleanup component reports an error.

The UI-independent settings module accepts and emits an explicit versioned
schema. It validates a strict field allowlist, migrates old schemas in memory,
returns privacy-safe recovery warnings, and replaces settings files atomically.
Invalid and newer-version files are preserved for diagnosis or recovery.

Interface text is routed through the UI-independent `i18n` module. English
source text is the stable key and Norwegian Bokmål is the first complete
translation catalogue. At startup, Skrivi resolves the stored Automatic,
English, or Norwegian choice before creating Qt widgets. Automatic follows the
Windows display language for Norwegian Windows installations and otherwise
falls back to English. Translation does not affect transcription language or
introduce network access.

Interface components subscribe through weak callbacks to language changes.
Existing Qt widgets retranslate in place, so the tray, settings, accessibility
labels, overlay state, and active model progress update without restarting
audio, transcription, or model work. Settings previews are reversible until
saved.

Live settings are coordinated as a recoverable operation. A microphone choice
is validated before activation. A replacement global key listener invalidates
and stops the previous generation before starting the next, so callbacks from a
late old listener cannot trigger dictation. If activation or persistence fails,
the previous runtime configuration is restored where possible.

## Interface implementation

PySide6 Essentials provides the tray, settings window and compact status
overlay. Qt's event loop stays on the main thread. Controller workers report
state through queued Qt signals, so model loading and transcription never
update widgets directly. The controller itself imports no Qt modules.

The overlay is a tool window that cannot accept focus or activate itself. It
uses the native system palette and a text symbol plus a message for every state,
so meaning does not depend on colour. Qt 6 supplies per-display DPI scaling.
Overlay placement uses the work area of the display containing the pointer and
supports displays with negative desktop coordinates.
