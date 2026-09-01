# Skrivi

Skrivi is a private, local push-to-talk dictation app for Windows 11.
Hold **Right Ctrl**, speak, and release the key. The complete transcription is
typed into the application that already has the cursor. Language, microphone,
and push-to-talk key can be changed from the tray's Settings window.

Press **Escape** while Skrivi is recording or transcribing to cancel the current
dictation. Recordings are automatically cancelled after five minutes so an
accidentally held key cannot leave the microphone recording indefinitely.
Exiting Skrivi stops keyboard and microphone input, cancels active model work,
and prevents an in-progress transcription from inserting text after exit.

The project is open source under the MIT licence. It is currently alpha
software: the core dictation workflow works, while configuration and broader
hardware testing are being developed.

## What this first version does

- Recognises English and Norwegian automatically, with fixed English, fixed
  Norwegian, and per-segment Multilingual modes available in Settings.
- Uses the Windows default microphone initially and can select another Windows
  input device.
- Offers verified local Tiny, Base, Small, and Medium models. Small remains the
  recommended default for CPU use.
- Shows per-model download and verification progress and allows an incomplete
  download to be cancelled without affecting installed models.
- Runs transcription locally on the CPU using `int8` inference.
- Shows a small indicator while loading, recording, and transcribing.
- Types Unicode directly through Windows, without putting text on the clipboard.
- Does not write recordings, transcripts, or content logs to disk.
- Provides a keyboard-operable Qt tray menu with status, Settings, and Exit.
- Provides complete English and Norwegian Bokmål interfaces, following the
  Windows display language by default with an explicit choice in Settings.
- Uses the native Windows palette and scaling, including high-DPI displays and
  high-contrast themes.

Whisper itself may add punctuation or omit hesitations. The app does not perform
any additional rewriting or filler-word removal.

## Fastest way to try it

1. Install the standard 64-bit Python 3.14 build from
   <https://www.python.org/downloads/windows/>. Do not select the experimental
   free-threaded build. Enable **Add Python to PATH** during installation.
2. Double-click `run_from_source.bat`.
3. On the first run, wait while the multilingual Small speech model downloads
   and is verified under `%LOCALAPPDATA%\Skrivi\models`. This is a one-time
   download of roughly 486 MB shared by later Skrivi versions.
4. Put the cursor in Word, Outlook, Notepad, or a browser text field.
5. Hold **Right Ctrl**, speak, then release it. Press **Escape** to cancel.

After the first model download, speech recognition does not require an internet
connection and no speech is sent to a cloud service.

## Build the portable executable

On a Windows 11 PC with standard 64-bit Python 3.14 installed:

1. Double-click `build_portable.bat`.
2. Wait for the dependencies and packaging step to finish.
3. Run the executable created in the `dist` folder.

The output is a single executable. Downloaded models are kept in the stable
per-user `%LOCALAPPDATA%\Skrivi\models` directory so later builds can reuse them.
Python is not required on PCs that only run the finished executable.

## Privacy behaviour

Audio is accumulated in memory only. After transcription, the audio arrays are
overwritten with zeros on a best-effort basis and references to the audio and
text are released. The app never copies dictated text to the clipboard.

The destination application can still retain what was typed through its own
undo history, autosave, cloud sync, or browser behaviour. Python cannot provide
forensic guarantees that an immutable string has vanished instantly from RAM.

## Expected limitations

- The first model load can take a little while on a CPU, particularly the first
  time the app starts.
- Very short phrases can be misidentified as the wrong language.
- A normal app cannot type into an administrator-elevated window. Run Skrivi as
  administrator only if that is genuinely required.
- Windows secure fields and some games intentionally reject simulated input.
- Only one dictation can be processed at a time. Right Ctrl is ignored while the
  model is loading or the previous dictation is being transcribed.

## Troubleshooting

- **Model unavailable:** open the tray menu and choose **Retry speech model**.
  If the selected model is not installed, open Settings → Models and download or
  select an installed model. Skrivi retries automatically after activation, so
  the application does not need to restart.
- **Transcription failed:** the recording is discarded from memory and Skrivi
  returns to Ready. Hold the dictation key and try again.
- **Microphone unavailable:** if a specifically selected microphone is
  disconnected, Skrivi temporarily uses Windows Default and automatically returns
  to the selected microphone when it reconnects. If no Windows input is
  available, check Windows Sound settings.
- **Nothing is typed:** test in Notepad first. Confirm the target app is not
  running as administrator while Skrivi is running normally.
- **Too slow:** the first candidate change is the model from `small` to `base` in
  Skrivi Settings → Models. Tiny is faster again. Accuracy will decrease.

## Development checks

From PowerShell, with the development requirements installed:

```powershell
python -m pytest
python -m ruff check .
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for the complete development workflow,
[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the design,
[docs/DEVELOPMENT_PLAN.md](docs/DEVELOPMENT_PLAN.md) for the live execution
checklist, [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) for the fast development
and preview loop, [docs/SETTINGS.md](docs/SETTINGS.md) for the versioned settings
schema, and [docs/ROADMAP.md](docs/ROADMAP.md) for planned releases. The
[local model guide](docs/MODELS.md) documents downloads, integrity checks,
offline operation, hardware guidance, and USB-folder import. The
project's longer-term credibility requirements are recorded in
[docs/QUALITY_BAR.md](docs/QUALITY_BAR.md) without presenting the current alpha
as school-ready assistive software.

## Licence

Skrivi is released under the [MIT licence](LICENSE). Third-party libraries and
downloaded speech models retain their own licences. PySide6 and Qt notices are
listed in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) and included with
packaged builds.
