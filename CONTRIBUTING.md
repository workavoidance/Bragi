# Contributing to Bragi

Thanks for helping improve private, local dictation on Windows.

## Development setup

Use standard 64-bit Python 3.14 on Windows 11.

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt -c constraints-windows.txt
python -m pip install -e . -c constraints-windows.txt
```

Run the checks before opening a pull request:

```powershell
python -m ruff format --check .
python -m ruff check .
python -m pytest
python -m compileall -q src tests tools
```

For quick UI feedback, controlled source restarts, and downloadable pull-request
artifacts, see [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md).

## Pull requests

- Keep changes focused and explain the user problem being solved.
- Add or update tests for behavioural changes.
- Do not add cloud transcription, telemetry, transcript storage, or audio
  retention without an explicit design discussion.
- Do not place dictated content in logs or exception reports.
- Update `CHANGELOG.md` for user-visible changes.
- Use a feature branch and allow CI to pass before merging.

Small fixes are welcome. For architectural changes, open an issue first so the
approach can be agreed before substantial work begins.
