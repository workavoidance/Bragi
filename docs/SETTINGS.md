# Settings storage

Bragi's settings layer is independent of the current and future user-interface
frameworks. It uses only the Python standard library and can be exercised in
unit tests without Windows audio, global hotkeys, Whisper, or PySide6.

## Locations

Normal user settings are stored at:

```text
%APPDATA%\Bragi\settings.json
```

Development builds use a separate file:

```text
%APPDATA%\Bragi\development\settings.json
```

Downloaded models remain separately stored under
`%LOCALAPPDATA%\Bragi\models`. Settings contain model identifiers, never model
data.

## Version 4 schema

```json
{
  "schema_version": 4,
  "language": "auto",
  "model": "small",
  "hotkey": "right_ctrl",
  "microphone": "windows_default",
  "overlay_enabled": true,
  "interface_language": "auto"
}
```

The defaults preserve Bragi's existing behaviour. Supported language values are
`auto`, `en`, `no`, and `multilingual`. Automatic detects one language for a
recording. Multilingual allows faster-whisper to detect the language again for
individual segments. Very short automatic-language recordings may not contain
enough speech for reliable detection.

Supported interface-language values are `auto`, `en`, and `nb`. Automatic uses
the Windows display language when it is Norwegian and otherwise uses English.
Users can explicitly select English or Norwegian Bokmål in Settings. An
interface-language change updates the open Settings window, tray, overlay, and
model status immediately. Cancel restores the previously saved language, while
Save persists the previewed choice.

Supported push-to-talk identifiers are `right_ctrl` and `f6` through `f12`.
Letters, Windows keys, modifier keys such as Alt, and common editing keys are
rejected. Microphones use `windows_default` or a stable `portaudio:`
identifier derived from the Windows audio host API and device name. A device is
resolved to its current PortAudio index when recording begins, so stored indexes
do not become stale.

Supported model identifiers are the packaged `tiny`, `base`, `small`, and
`medium` catalogue. Arbitrary repository names are rejected. Settings store
only the selected identifier; model files and integrity manifests remain under
`%LOCALAPPDATA%\Bragi\models`.

## Validation and recovery

The current schema requires exactly the documented fields and validates their
types and basic safety constraints. Unknown fields are rejected. A missing file
uses defaults without a warning. Malformed JSON, missing fields, invalid values,
and unreadable files use defaults and return a short warning suitable for the
future interface.

Warnings never include the rejected value, file contents, or underlying
exception text. Bragi preserves an invalid or newer-version file rather than
silently overwriting it.

## Migrations

Every document has an integer schema version. Migrations are applied in order in
memory before validation. Version 0 is the reserved unversioned prototype shape
and maps `language_mode`, `model_name`, and `show_overlay` to their version 1
equivalents. Version 1 documents migrate to version 2 without changing their
existing choices. Version 2 documents migrate to version 3, which restricts the
model field to Bragi's trusted local catalogue. Version 3 documents migrate to
version 4 with automatic Windows interface-language selection.

A migrated document is written in the current format the next time settings are
explicitly saved. A schema newer than this Bragi version is never downgraded or
overwritten automatically.

## Atomic writes

Saving writes a complete UTF-8 JSON document to a temporary file in the same
directory, flushes it to disk, and then replaces `settings.json` with
`os.replace`. If writing or replacement fails, the previous settings file is
left intact and the temporary file is removed on a best-effort basis.

Bragi has a single-instance application model, so concurrent user-interface
writes are not supported or required.

## Current interface support

The v0.2 settings window can change dictation language, interface language,
microphone, push-to-talk key, speech model, and overlay visibility. Dictation
language changes affect the next recording. Interface language changes are
previewed immediately and do not restart dictation or model activity.
Microphones are enumerated locally and validated before a selection becomes
active. Hotkey
capture accepts a deliberately small safe set and replaces the active global
listener before saving, with rollback if activation fails. These changes do not
require an application restart. The Models tab shows local installation state,
download size, RAM and CPU guidance, and controls for download, activation,
removal, and verified folder import.

## Privacy and offline operation

The settings schema contains only configuration values. It has no audio,
transcript, clipboard, history, telemetry, account, or remote-service fields.
The serializer writes only its explicit allowlist, and the loader rejects
unknown fields rather than retaining them.

Loading, validating, migrating, and saving settings perform no network access.
