# Privacy model

Bragi is designed to perform speech recognition locally.

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
is outside Bragi's control.

The recommended Small model is downloaded from its Hugging Face distribution
host during initial setup if it is not already cached. Other models are
downloaded only after the user selects Download. The distribution host can see
ordinary connection metadata such as the requesting IP address during that
download. Bragi sends no recording, transcript, account identifier, or usage
telemetry.

After a verified download completes, Bragi loads the model by local filesystem
path. Transcription, installed-model selection, verification, and removal work
offline and do not fetch a remote model catalogue.
