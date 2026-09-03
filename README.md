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

- Offers Automatic, Norwegian, and English dictation modes. Automatic compares
  only Norwegian and English for each recording.
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
- Can start quietly when the current user signs in, when explicitly enabled in
  Settings. This is off by default and requires no administrator rights.
- Uses the native Windows palette and scaling, including high-DPI displays and
  high-contrast themes.

Whisper itself may add punctuation or omit hesitations. The app does not perform
any additional rewriting or filler-word removal.

## Install Skrivi

1. [Download the Skrivi v0.2 alpha installer for Windows 11](https://github.com/workavoidance/Skrivi/releases/download/v0.2.0-alpha.3/Skrivi-v0.2.0-alpha.3-windows-x64-setup.exe).
2. Open the downloaded installer. This alpha is not code-signed yet, so Windows
   may show SmartScreen. If you trust this project, choose **More info**, then
   **Run anyway**.
3. Complete the short installer and start Skrivi from the Start menu.
4. On the first run, wait while the multilingual Small speech model downloads
   and is verified under `%LOCALAPPDATA%\Skrivi\models`. This is a one-time
   download of roughly 486 MB shared by later Skrivi versions.
5. Put the cursor in Word, Outlook, Notepad, or a browser text field.
6. Hold **Right Ctrl**, speak, then release it. Press **Escape** to cancel.

After the first model download, speech recognition does not require an internet
connection and no speech is sent to a cloud service.

The installer needs no administrator permission and provides standard Start
menu and uninstall entries. Advanced users can instead download the portable
ZIP from the [release page](https://github.com/workavoidance/Skrivi/releases/tag/v0.2.0-alpha.3)
or follow [the development guide](docs/DEVELOPMENT.md) to run from source.

## Build the portable executable

On a Windows 11 PC with standard 64-bit Python 3.14 installed:

1. Double-click `build_portable.bat`.
2. Wait for the dependencies and packaging step to finish.
3. Run the executable created in the `dist` folder.

The output is a single executable. Downloaded models are kept in the stable
per-user `%LOCALAPPDATA%\Skrivi\models` directory so later builds can reuse them.
Python is not required on PCs that only run the finished executable.

## Build the Windows installer

The conventional installer uses a one-folder application build so Skrivi does
not unpack its full Python runtime on every launch. On Windows 11, install
Python 3.14 and Inno Setup 6, then run:

```bat
build_installer.bat
```

The installer is written to `dist\installer`. It installs for the current user
under `%LOCALAPPDATA%\Programs\Skrivi`, adds Start menu and uninstall entries,
and does not request administrator rights. Settings and downloaded models stay
in their existing application-data directories, so installing, upgrading, or
uninstalling the program does not silently delete user choices or large model
downloads.

## Privacy behaviour

Audio is accumulated in memory only. After transcription, the audio arrays are
overwritten with zeros on a best-effort basis and references to the audio and
text are released. The app never copies dictated text to the clipboard.

The destination application can still retain what was typed through its own
undo history, autosave, cloud sync, or browser behaviour. Python cannot provide
forensic guarantees that an immutable string has vanished instantly from RAM.

## Code signing policy

Current Skrivi releases are not code-signed. The project's
[code signing policy](CODE_SIGNING_POLICY.md) documents the Windows artifacts,
team roles, privacy information, and manual approval process proposed for the
SignPath Foundation open-source programme.

## Expected limitations

- The first model load can take a little while on a CPU, particularly the first
  time the app starts.
- Very short phrases can still be misidentified as Norwegian or English.
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
