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

## Version 1 schema

```json
{
  "schema_version": 1,
  "language": "auto",
  "model": "small",
  "hotkey": "right_ctrl",
  "microphone": "windows_default",
  "overlay_enabled": true
}
```

The defaults preserve Bragi's existing behaviour. Supported language values in
this schema are `auto`, `en`, and `no`. The later settings interface and model
catalogue will constrain selectable values further before saving them.

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
equivalents.

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

## Privacy and offline operation

The settings schema contains only configuration values. It has no audio,
transcript, clipboard, history, telemetry, account, or remote-service fields.
The serializer writes only its explicit allowlist, and the loader rejects
unknown fields rather than retaining them.

Loading, validating, migrating, and saving settings perform no network access.
