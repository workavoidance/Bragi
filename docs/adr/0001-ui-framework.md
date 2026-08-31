# ADR 0001: Use PySide6 for the configurable UI

- Status: Accepted
- Date: 2026-08-31

## Context

The initial Tkinter overlay proved the speech pipeline but is not a strong base
for model management, settings, progress, accessibility and a polished tray
experience.

## Decision

Use PySide6 for the v0.2 settings window, tray icon and future interface work.
Keep the transcription and Windows integration layers independent from Qt.

## Consequences

- The application gains mature widgets, high-DPI support, accessibility and
  reliable background-worker integration.
- Release size increases because Qt libraries are bundled.
- PySide6 and Qt licence notices must ship with releases. Project code remains
  MIT licensed; dependencies retain their own licences.
- Migration happens behind the existing UI interface and must not alter the
  proven speech pipeline in the same change.
