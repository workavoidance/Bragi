from __future__ import annotations

import threading
from dataclasses import dataclass

import numpy as np


@dataclass
class CapturedAudio:
    samples: np.ndarray
    sample_rate: int


class AudioRecorder:
    """Capture the Windows default input device into memory only."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._blocks: list[np.ndarray] = []
        self._stream = None
        self._sample_rate = 0

    @property
    def is_recording(self) -> bool:
        return self._stream is not None

    def start(self) -> None:
        import sounddevice as sd

        if self._stream is not None:
            return
        device_info = sd.query_devices(kind="input")
        sample_rate = int(round(float(device_info["default_samplerate"])))
        if sample_rate <= 0:
            raise RuntimeError("The default microphone reported an invalid sample rate")

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

        stream = sd.InputStream(
            device=None,
            channels=1,
            samplerate=sample_rate,
            dtype="float32",
            callback=callback,
        )
        try:
            stream.start()
        except Exception:
            stream.close()
            raise
        self._stream = stream

    def stop(self) -> CapturedAudio:
        stream = self._stream
        self._stream = None
        if stream is None:
            return CapturedAudio(np.empty(0, dtype=np.float32), self._sample_rate)
        try:
            stream.stop()
        finally:
            stream.close()

        with self._lock:
            blocks = self._blocks
            self._blocks = []
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
