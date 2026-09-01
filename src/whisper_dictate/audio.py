from __future__ import annotations

import threading
from dataclasses import dataclass
from urllib.parse import quote, unquote

import numpy as np

from whisper_dictate.i18n import tr

WINDOWS_DEFAULT_MICROPHONE = "windows_default"
MICROPHONE_ID_PREFIX = "portaudio:"


class MicrophoneUnavailableError(RuntimeError):
    """Raised when the selected input device cannot currently be used."""


@dataclass(frozen=True)
class MicrophoneDevice:
    identifier: str
    name: str
    host_api: str
    device_index: int | None

    @property
    def label(self) -> str:
        if self.identifier == WINDOWS_DEFAULT_MICROPHONE:
            return tr("Windows Default")
        return f"{self.name} ({self.host_api})"


@dataclass
class CapturedAudio:
    samples: np.ndarray
    sample_rate: int


def microphone_identifier(host_api: str, name: str) -> str:
    return f"{MICROPHONE_ID_PREFIX}{quote(host_api, safe='')}:{quote(name, safe='')}"


def microphone_name_from_identifier(identifier: str) -> str:
    if identifier == WINDOWS_DEFAULT_MICROPHONE:
        return tr("Windows Default")
    if not identifier.startswith(MICROPHONE_ID_PREFIX):
        return tr("Unknown microphone")
    encoded = identifier.removeprefix(MICROPHONE_ID_PREFIX)
    _separator, _colon, encoded_name = encoded.partition(":")
    return unquote(encoded_name) if encoded_name else tr("Unknown microphone")


def _sounddevice():
    import sounddevice as sd

    return sd


def list_input_devices(backend=None) -> list[MicrophoneDevice]:
    """Return the current input devices with a stable, human-readable identity."""
    sd = backend or _sounddevice()
    devices = sd.query_devices()
    host_apis = sd.query_hostapis()
    result = [
        MicrophoneDevice(
            identifier=WINDOWS_DEFAULT_MICROPHONE,
            name="Windows Default",
            host_api="Windows",
            device_index=None,
        )
    ]
    seen = {WINDOWS_DEFAULT_MICROPHONE}
    for index, device in enumerate(devices):
        if int(device.get("max_input_channels", 0)) <= 0:
            continue
        host_index = int(device.get("hostapi", -1))
        if 0 <= host_index < len(host_apis):
            host_name = str(host_apis[host_index].get("name", "Windows audio"))
        else:
            host_name = "Windows audio"
        name = str(device.get("name", f"Input {index}"))
        identifier = microphone_identifier(host_name, name)
        if identifier in seen:
            continue
        seen.add(identifier)
        result.append(
            MicrophoneDevice(
                identifier=identifier,
                name=name,
                host_api=host_name,
                device_index=index,
            )
        )
    return result


def resolve_input_device(identifier: str, backend=None) -> MicrophoneDevice:
    sd = backend or _sounddevice()
    if identifier == WINDOWS_DEFAULT_MICROPHONE:
        try:
            sd.query_devices(kind="input")
        except Exception as error:
            raise MicrophoneUnavailableError(
                tr(
                    "Windows Default microphone is unavailable. Check Windows Sound "
                    "settings."
                )
            ) from error
        return MicrophoneDevice(identifier, "Windows Default", "Windows", None)

    try:
        devices = list_input_devices(sd)
    except Exception as error:
        raise MicrophoneUnavailableError(
            tr(
                "Microphones could not be checked. Try Windows Default or reconnect "
                "the device."
            )
        ) from error
    for device in devices:
        if device.identifier == identifier:
            return device
    raise MicrophoneUnavailableError(
        tr(
            "The selected microphone is unavailable. Open Settings and choose another "
            "microphone or Windows Default."
        )
    )


class AudioRecorder:
    """Capture one selected Windows input device into memory only."""

    def __init__(
        self,
        microphone: str = WINDOWS_DEFAULT_MICROPHONE,
        *,
        backend=None,
    ) -> None:
        self._lock = threading.Lock()
        self._configuration_lock = threading.Lock()
        self._blocks: list[np.ndarray] = []
        self._stream = None
        self._sample_rate = 0
        self._microphone = microphone
        self._using_default_fallback = False
        self._backend = backend

    @property
    def is_recording(self) -> bool:
        return self._stream is not None

    @property
    def microphone(self) -> str:
        with self._configuration_lock:
            return self._microphone

    @property
    def using_default_fallback(self) -> bool:
        with self._configuration_lock:
            return self._using_default_fallback

    def set_microphone(self, identifier: str) -> None:
        with self._configuration_lock:
            self._microphone = identifier

    def validate_microphone(self, identifier: str) -> None:
        resolve_input_device(identifier, self._backend)

    def start(self) -> None:
        sd = self._backend or _sounddevice()
        if self._stream is not None:
            return
        with self._configuration_lock:
            selected = self._microphone
        using_default_fallback = False
        try:
            device = resolve_input_device(selected, sd)
        except MicrophoneUnavailableError:
            if selected == WINDOWS_DEFAULT_MICROPHONE:
                raise
            device = resolve_input_device(WINDOWS_DEFAULT_MICROPHONE, sd)
            using_default_fallback = True
        try:
            if device.device_index is None:
                device_info = sd.query_devices(kind="input")
            else:
                device_info = sd.query_devices(device=device.device_index, kind="input")
        except Exception as error:
            raise MicrophoneUnavailableError(
                tr(
                    "The selected microphone is unavailable. Open Settings and choose "
                    "another microphone or Windows Default."
                )
            ) from error
        sample_rate = int(round(float(device_info["default_samplerate"])))
        if sample_rate <= 0:
            raise MicrophoneUnavailableError(
                tr(
                    "The selected microphone reported an invalid sample rate. Choose "
                    "another microphone in Settings."
                )
            )

        with self._lock:
            self._blocks.clear()
        self._sample_rate = sample_rate

        def callback(indata, frames, time_info, status) -> None:
            del frames, time_info
            if status.input_overflow:
                # Continue recording. A short overflow is preferable to losing
                # the entire utterance, and no audio is written to disk.
                pass
            with self._lock:
                self._blocks.append(indata.copy())

        stream = None
        try:
            stream = sd.InputStream(
                device=device.device_index,
                channels=1,
                samplerate=sample_rate,
                dtype="float32",
                callback=callback,
            )
            stream.start()
        except Exception as error:
            if stream is not None:
                try:
                    stream.close()
                except Exception:
                    pass
            raise MicrophoneUnavailableError(
                tr("The microphone could not start. Check Windows Sound settings.")
            ) from error
        self._stream = stream
        with self._configuration_lock:
            self._using_default_fallback = using_default_fallback

    def stop(self) -> CapturedAudio:
        stream = self._stream
        self._stream = None
        if stream is None:
            return CapturedAudio(np.empty(0, dtype=np.float32), self._sample_rate)
        stream_error = None
        try:
            stream.stop()
        except Exception as error:
            stream_error = error
        try:
            stream.close()
        except Exception as error:
            if stream_error is None:
                stream_error = error

        with self._lock:
            blocks = self._blocks
            self._blocks = []
        if stream_error is not None:
            for block in blocks:
                block.fill(0)
            raise MicrophoneUnavailableError(
                tr(
                    "The microphone was disconnected. This recording was discarded; "
                    "try dictating again."
                )
            ) from stream_error
        if not blocks:
            samples = np.empty(0, dtype=np.float32)
        else:
            samples = (
                np.concatenate(blocks, axis=0)
                .reshape(-1)
                .astype(np.float32, copy=False)
            )
        return CapturedAudio(samples=samples, sample_rate=self._sample_rate)

    def cancel(self) -> None:
        captured = self.stop()
        if captured.samples.size:
            captured.samples.fill(0)
