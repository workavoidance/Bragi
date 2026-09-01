from __future__ import annotations

import json
import os
import tempfile
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from whisper_dictate.hotkeys import (
    DEFAULT_HOTKEY,
    HotkeyValidationError,
    validate_hotkey,
)
from whisper_dictate.i18n import InterfaceLanguage
from whisper_dictate.models import MODEL_BY_ID
from whisper_dictate.runtime import settings_directory

CURRENT_SCHEMA_VERSION = 4
SETTINGS_FILENAME = "settings.json"
READ_ERRORS = (OSError, UnicodeError)
JSON_ERRORS = (json.JSONDecodeError, RecursionError)
WRITE_ERRORS = (OSError, UnicodeError)
LANGUAGE_ERRORS = (ValueError, TypeError)

MALFORMED_WARNING = "Settings are damaged; safe defaults are in use."
UNREADABLE_WARNING = "Settings could not be read; safe defaults are in use."
INVALID_WARNING = "Settings contain unsupported values; safe defaults are in use."
NEWER_VERSION_WARNING = (
    "Settings were written by a newer Skrivi version; safe defaults are in use."
)


class LanguageMode(StrEnum):
    AUTOMATIC = "auto"
    ENGLISH = "en"
    NORWEGIAN = "no"
    MULTILINGUAL = "multilingual"


class SettingsValidationError(ValueError):
    """Raised when a settings document does not match the current schema."""


class UnsupportedSettingsVersion(SettingsValidationError):
    """Raised when a settings document is newer than this Skrivi version."""


class SettingsWriteError(OSError):
    """Raised when an atomic settings write cannot be completed."""


def _validated_text(value: object, field: str, maximum_length: int) -> str:
    if not isinstance(value, str):
        raise SettingsValidationError(f"{field} must be text")
    if not value or value != value.strip() or len(value) > maximum_length:
        raise SettingsValidationError(f"{field} has an invalid length")
    if any(ord(character) < 32 or ord(character) == 127 for character in value):
        raise SettingsValidationError(f"{field} contains control characters")
    return value


@dataclass(frozen=True)
class UserSettings:
    schema_version: int = CURRENT_SCHEMA_VERSION
    language: LanguageMode = LanguageMode.AUTOMATIC
    model: str = "small"
    hotkey: str = "right_ctrl"
    microphone: str = "windows_default"
    overlay_enabled: bool = True
    interface_language: InterfaceLanguage = InterfaceLanguage.AUTOMATIC

    @classmethod
    def from_document(cls, document: Mapping[str, object]) -> UserSettings:
        expected = {
            "schema_version",
            "language",
            "model",
            "hotkey",
            "microphone",
            "overlay_enabled",
            "interface_language",
        }
        if set(document) != expected:
            raise SettingsValidationError("settings fields do not match the schema")

        schema_version = document["schema_version"]
        if (
            isinstance(schema_version, bool)
            or not isinstance(schema_version, int)
            or schema_version != CURRENT_SCHEMA_VERSION
        ):
            raise SettingsValidationError("schema version is invalid")

        try:
            language = LanguageMode(document["language"])
        except LANGUAGE_ERRORS:
            raise SettingsValidationError("language is unsupported") from None

        model = _validated_text(document["model"], "model", 128)
        if model not in MODEL_BY_ID:
            raise SettingsValidationError("model is unsupported")
        hotkey = _validated_text(document["hotkey"], "hotkey", 64)
        try:
            hotkey = validate_hotkey(hotkey)
        except HotkeyValidationError:
            raise SettingsValidationError("hotkey is unsupported") from None
        microphone = _validated_text(document["microphone"], "microphone", 512)
        if microphone != "windows_default" and not microphone.startswith("portaudio:"):
            raise SettingsValidationError("microphone identifier is unsupported")
        overlay_enabled = document["overlay_enabled"]
        if not isinstance(overlay_enabled, bool):
            raise SettingsValidationError("overlay_enabled must be true or false")
        try:
            interface_language = InterfaceLanguage(document["interface_language"])
        except LANGUAGE_ERRORS:
            raise SettingsValidationError("interface language is unsupported") from None

        return cls(
            schema_version=CURRENT_SCHEMA_VERSION,
            language=language,
            model=model,
            hotkey=hotkey,
            microphone=microphone,
            overlay_enabled=overlay_enabled,
            interface_language=interface_language,
        )

    def to_document(self) -> dict[str, object]:
        language = (
            self.language.value
            if isinstance(self.language, LanguageMode)
            else self.language
        )
        interface_language = (
            self.interface_language.value
            if isinstance(self.interface_language, InterfaceLanguage)
            else self.interface_language
        )
        return {
            "schema_version": self.schema_version,
            "language": language,
            "model": self.model,
            "hotkey": self.hotkey,
            "microphone": self.microphone,
            "overlay_enabled": self.overlay_enabled,
            "interface_language": interface_language,
        }


@dataclass(frozen=True)
class SettingsLoadResult:
    settings: UserSettings
    warning: str | None = None
    migrated_from: int | None = None

    @property
    def recovered_with_defaults(self) -> bool:
        return self.warning is not None


def _migrate_v0_to_v1(document: dict[str, object]) -> dict[str, object]:
    migrated = dict(document)
    aliases = {
        "language_mode": "language",
        "model_name": "model",
        "show_overlay": "overlay_enabled",
    }
    for old_name, new_name in aliases.items():
        if old_name in migrated and new_name not in migrated:
            migrated[new_name] = migrated.pop(old_name)
    migrated["schema_version"] = 1
    return migrated


def _migrate_v1_to_v2(document: dict[str, object]) -> dict[str, object]:
    migrated = dict(document)
    migrated["schema_version"] = 2
    return migrated


def _migrate_v2_to_v3(document: dict[str, object]) -> dict[str, object]:
    migrated = dict(document)
    migrated["schema_version"] = 3
    return migrated


def _migrate_v3_to_v4(document: dict[str, object]) -> dict[str, object]:
    migrated = dict(document)
    migrated["interface_language"] = InterfaceLanguage.AUTOMATIC.value
    migrated["schema_version"] = 4
    return migrated


MIGRATIONS = {
    0: _migrate_v0_to_v1,
    1: _migrate_v1_to_v2,
    2: _migrate_v2_to_v3,
    3: _migrate_v3_to_v4,
}


def migrate_document(
    document: Mapping[str, object],
) -> tuple[dict[str, object], int | None]:
    migrated = dict(document)
    raw_version = migrated.get("schema_version", 0)
    if isinstance(raw_version, bool) or not isinstance(raw_version, int):
        raise SettingsValidationError("schema version must be an integer")
    if raw_version < 0:
        raise SettingsValidationError("schema version cannot be negative")
    if raw_version > CURRENT_SCHEMA_VERSION:
        raise UnsupportedSettingsVersion("settings version is newer than supported")

    original_version = raw_version
    while raw_version < CURRENT_SCHEMA_VERSION:
        migration = MIGRATIONS.get(raw_version)
        if migration is None:
            raise SettingsValidationError(
                "no migration exists for the settings version"
            )
        migrated = migration(migrated)
        raw_version += 1

    # Right Alt was briefly available in development builds, but it is AltGr
    # on common Norwegian keyboards and cannot yet be used reliably. Preserve
    # every other setting while returning those test installations to default.
    if migrated.get("hotkey") == "right_alt":
        migrated["hotkey"] = DEFAULT_HOTKEY

    migrated_from = (
        original_version if original_version < CURRENT_SCHEMA_VERSION else None
    )
    return migrated, migrated_from


class SettingsStore:
    def __init__(self, path: Path) -> None:
        self.path = path

    @classmethod
    def for_user(
        cls,
        *,
        development: bool = False,
        environment: Mapping[str, str] | None = None,
        home: Path | None = None,
    ) -> SettingsStore:
        directory = settings_directory(
            development=development,
            environment=environment,
            home=home,
        )
        return cls(directory / SETTINGS_FILENAME)

    def load(self) -> SettingsLoadResult:
        try:
            raw_text = self.path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return SettingsLoadResult(UserSettings())
        except READ_ERRORS:
            return SettingsLoadResult(UserSettings(), warning=UNREADABLE_WARNING)

        try:
            document = json.loads(raw_text)
        except JSON_ERRORS:
            return SettingsLoadResult(UserSettings(), warning=MALFORMED_WARNING)
        if not isinstance(document, dict):
            return SettingsLoadResult(UserSettings(), warning=INVALID_WARNING)

        try:
            migrated, migrated_from = migrate_document(document)
            settings = UserSettings.from_document(migrated)
        except UnsupportedSettingsVersion:
            return SettingsLoadResult(UserSettings(), warning=NEWER_VERSION_WARNING)
        except SettingsValidationError:
            return SettingsLoadResult(UserSettings(), warning=INVALID_WARNING)
        return SettingsLoadResult(settings, migrated_from=migrated_from)

    def save(self, settings: UserSettings) -> None:
        validated = UserSettings.from_document(settings.to_document())
        payload = (
            json.dumps(
                validated.to_document(),
                ensure_ascii=False,
                indent=2,
            )
            + "\n"
        )
        descriptor = -1
        temporary_path: Path | None = None
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            descriptor, temporary_name = tempfile.mkstemp(
                prefix=f".{self.path.name}.",
                suffix=".tmp",
                dir=self.path.parent,
            )
            temporary_path = Path(temporary_name)
            with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as file:
                descriptor = -1
                file.write(payload)
                file.flush()
                os.fsync(file.fileno())
            os.replace(temporary_path, self.path)
            temporary_path = None
        except WRITE_ERRORS as error:
            raise SettingsWriteError("Skrivi could not save settings safely") from error
        finally:
            if descriptor >= 0:
                try:
                    os.close(descriptor)
                except OSError:
                    pass
            if temporary_path is not None:
                try:
                    temporary_path.unlink(missing_ok=True)
                except OSError:
                    pass
