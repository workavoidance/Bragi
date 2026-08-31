# Privacy model

Whisper Dictate is designed to perform speech recognition locally.

## Data that persists

- Downloaded model files.
- User-selected settings.
- Application version and non-content diagnostic information, if diagnostics
  are introduced in a future version.

## Data that does not persist

- Microphone recordings.
- Transcripts.
- Clipboard copies of dictated text.
- Cloud speech-recognition requests.

Captured audio is held in process memory. The application overwrites mutable
audio buffers after processing on a best-effort basis. Python cannot guarantee
forensic erasure of immutable strings from memory.

The destination application may retain inserted text through undo history,
autosave, browser storage, synchronisation, or its own telemetry. That behaviour
is outside Whisper Dictate's control.

The model is downloaded from its distribution host the first time it is used.
After the download completes, transcription itself works offline.
