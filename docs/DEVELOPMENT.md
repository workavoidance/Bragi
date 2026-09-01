# Fast development and preview workflow

Skrivi has two local development modes and an automated Windows preview build.
They are intended to shorten feedback cycles without weakening the privacy or
offline requirements.

## Requirements

- Windows 11
- Standard 64-bit Python 3.14, not the experimental free-threaded build
- Internet access the first time dependencies or a selected model are installed

The launcher installs dependencies only when `pyproject.toml`, a requirements
file, or the Windows constraints file changes.

## Preview the interface without speech services

From File Explorer, open a terminal in the repository and run:

```bat
dev.bat preview
```

This mode does not load Whisper, access a microphone, register a global hotkey,
or insert text. Use **Settings** in the Skrivi tray menu to inspect the window,
then use **Preview state** to display the loading, ready, recording,
transcribing, no-speech, and error indicators.

The Models tab displays the complete interface and catalogue in preview mode,
but Download, Use, Remove, and Import are disabled so preview cannot access the
network or model files.

Changes to Python files under `src` cause the managed preview process to restart
automatically. The launcher waits for the old child process to stop before it
starts the replacement. Press Ctrl+C in the launcher window to finish.

## Run the real application from source

Run:

```bat
dev.bat
```

This starts the actual microphone, local Whisper, hotkey, and text-insertion
pipeline from an editable installation. Source changes trigger the same
controlled restart. The tray title contains `DEV` and the current short Git
commit so the tested source can be identified.

Restarting the real development process currently reloads the model. Use preview
mode for rapid visual changes and real mode for end-to-end acceptance checks.

## Persistent and isolated development data

Models are shared across normal, development, and pull-request preview builds:

```text
%LOCALAPPDATA%\Skrivi\models
```

Normal settings live under `%APPDATA%\Skrivi`. Development settings have a
separate location under `%APPDATA%\Skrivi\development`, preventing a test
schema or value from damaging a normal user's settings.

The first real run may download the selected model. Once the dependencies and
model are installed, the application continues to work without internet access.
Preview mode itself never uses speech services or requires a model.

## Test a pull request build

Every pull request starts the **Windows preview** GitHub Actions workflow. It
produces a ZIP named in this form:

```text
Skrivi-PR-11-a1b2c3d-windows-x64.zip
```

Download the artifact from the pull request's Actions run, extract the complete
ZIP, and run the executable. Keep `BUILD_INFO.json` beside the executable. It
marks the build as a development preview and supplies the PR and commit identity
shown in the tray title.

Preview artifacts are retained for seven days and are never published as
releases. They are unsigned development builds and may trigger Windows security
warnings.

For interface changes, complete
[the Windows interface acceptance checklist](UI_TEST_CHECKLIST.md) against the
portable preview before merge. Automated tests cover widget semantics,
thread-safe status delivery and negative-coordinate overlay placement; Windows
Narrator, scaling, high-contrast and mixed-DPI behaviour still require a real
Windows test.
