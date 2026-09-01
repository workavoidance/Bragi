from __future__ import annotations

import pytest

from whisper_dictate.audio import (
    WINDOWS_DEFAULT_MICROPHONE,
    MicrophoneUnavailableError,
    list_input_devices,
    microphone_identifier,
    microphone_name_from_identifier,
    resolve_input_device,
)


class FakeAudioBackend:
    def __init__(self) -> None:
        self.devices = [
            {
                "name": "Microphone æøå",
                "hostapi": 0,
                "max_input_channels": 1,
                "default_samplerate": 48_000,
            },
            {
                "name": "Speakers",
                "hostapi": 0,
                "max_input_channels": 0,
                "default_samplerate": 48_000,
            },
        ]
        self.hostapis = [{"name": "Windows WASAPI"}]

    def query_devices(self, device=None, kind=None):
        if device is None and kind is None:
            return self.devices
        if device is None and kind == "input":
            return self.devices[0]
        return self.devices[device]

    def query_hostapis(self):
        return self.hostapis


def test_input_devices_include_windows_default_and_unicode_names() -> None:
    devices = list_input_devices(FakeAudioBackend())

    assert devices[0].identifier == WINDOWS_DEFAULT_MICROPHONE
    assert devices[0].label == "Windows Default"
    assert len(devices) == 2
    assert devices[1].label == "Microphone æøå (Windows WASAPI)"
    assert microphone_name_from_identifier(devices[1].identifier) == "Microphone æøå"


def test_selected_microphone_resolves_to_current_device_index() -> None:
    backend = FakeAudioBackend()
    identifier = microphone_identifier("Windows WASAPI", "Microphone æøå")

    device = resolve_input_device(identifier, backend)

    assert device.device_index == 0


def test_disconnected_microphone_has_actionable_recovery() -> None:
    backend = FakeAudioBackend()
    missing = microphone_identifier("Windows WASAPI", "Disconnected mic")

    with pytest.raises(MicrophoneUnavailableError, match="Windows Default"):
        resolve_input_device(missing, backend)
