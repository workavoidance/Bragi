from __future__ import annotations

import numpy as np
import pytest

from whisper_dictate.audio import (
    WINDOWS_DEFAULT_MICROPHONE,
    AudioRecorder,
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


class FakeInputStream:
    def __init__(self, backend, **kwargs) -> None:
        self.backend = backend
        self.device = kwargs["device"]
        self.samplerate = kwargs["samplerate"]
        self.callback = kwargs["callback"]
        self.started = False
        self.closed = False

    def start(self) -> None:
        self.started = True

    def stop(self) -> None:
        if self.backend.fail_stop:
            raise RuntimeError("device removed")

    def close(self) -> None:
        self.closed = True

    def emit(self, samples: np.ndarray) -> None:
        status = type("Status", (), {"input_overflow": False})()
        self.callback(samples.reshape(-1, 1), len(samples), None, status)


class DynamicAudioBackend(FakeAudioBackend):
    def __init__(self) -> None:
        super().__init__()
        self.default_index = 0
        self.fail_stop = False
        self.streams: list[FakeInputStream] = []

    def query_devices(self, device=None, kind=None):
        if device is None and kind == "input":
            return self.devices[self.default_index]
        return super().query_devices(device, kind)

    def InputStream(self, **kwargs):
        stream = FakeInputStream(self, **kwargs)
        self.streams.append(stream)
        return stream

    def add_usb_microphone(self) -> str:
        self.devices.append(
            {
                "name": "USB microphone",
                "hostapi": 0,
                "max_input_channels": 1,
                "default_samplerate": 44_100,
            }
        )
        return microphone_identifier("Windows WASAPI", "USB microphone")


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


def test_disconnected_selection_temporarily_uses_windows_default() -> None:
    backend = DynamicAudioBackend()
    missing = microphone_identifier("Windows WASAPI", "USB microphone")
    recorder = AudioRecorder(missing, backend=backend)

    recorder.start()

    assert recorder.microphone == missing
    assert recorder.using_default_fallback is True
    assert backend.streams[-1].device is None
    recorder.stop()


def test_preferred_microphone_is_reused_after_reconnection() -> None:
    backend = DynamicAudioBackend()
    preferred = microphone_identifier("Windows WASAPI", "USB microphone")
    recorder = AudioRecorder(preferred, backend=backend)
    recorder.start()
    recorder.stop()

    assert recorder.using_default_fallback is True

    backend.add_usb_microphone()
    recorder.start()

    assert recorder.using_default_fallback is False
    assert backend.streams[-1].device == 2
    recorder.stop()


def test_windows_default_is_resolved_again_for_each_recording() -> None:
    backend = DynamicAudioBackend()
    backend.add_usb_microphone()
    recorder = AudioRecorder(backend=backend)

    recorder.start()
    recorder.stop()
    backend.default_index = 2
    recorder.start()
    recorder.stop()

    assert [stream.samplerate for stream in backend.streams] == [48_000, 44_100]
    assert all(stream.device is None for stream in backend.streams)


def test_device_removal_during_recording_discards_buffered_audio() -> None:
    backend = DynamicAudioBackend()
    recorder = AudioRecorder(backend=backend)
    recorder.start()
    backend.streams[-1].emit(np.full(128, 0.5, dtype=np.float32))
    backend.fail_stop = True

    with pytest.raises(MicrophoneUnavailableError, match="recording was discarded"):
        recorder.stop()

    assert recorder.is_recording is False
    assert recorder._blocks == []
