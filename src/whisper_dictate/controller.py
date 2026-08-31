from __future__ import annotations

import enum
import threading
import time

from whisper_dictate.audio import AudioRecorder, CapturedAudio
from whisper_dictate.config import AppConfig
from whisper_dictate.core import audio_rms, resample_audio


class AppState(enum.Enum):
    LOADING = "loading"
    READY = "ready"
    RECORDING = "recording"
    TRANSCRIBING = "transcribing"
    ERROR = "error"
    STOPPED = "stopped"


class DictationController:
    def __init__(
        self,
        config: AppConfig,
        recorder: AudioRecorder,
        transcriber,
        injector,
        indicator,
        hotkey_listener,
    ) -> None:
        self._config = config
        self._recorder = recorder
        self._transcriber = transcriber
        self._injector = injector
        self._indicator = indicator
        self._hotkey_listener = hotkey_listener
        self._state = AppState.LOADING
        self._lock = threading.Lock()
        self._stopping = threading.Event()

    @property
    def state(self) -> AppState:
        with self._lock:
            return self._state

    def _set_state(self, state: AppState) -> None:
        with self._lock:
            self._state = state

    def start(self) -> None:
        self._indicator.post("loading")
        self._hotkey_listener.start()
        threading.Thread(target=self._load_model, daemon=True).start()

    def _load_model(self) -> None:
        try:
            self._transcriber.load()
        except Exception:
            self._set_state(AppState.ERROR)
            self._indicator.post(
                "error", "Model unavailable — check internet, then restart"
            )
            return
        if not self._stopping.is_set():
            self._set_state(AppState.READY)
            self._indicator.post("ready")

    def on_hotkey_press(self) -> None:
        with self._lock:
            if self._state is not AppState.READY:
                return
            self._state = AppState.RECORDING
        try:
            self._recorder.start()
        except Exception:
            self._set_state(AppState.READY)
            self._indicator.post("error", "Default microphone is unavailable")
            return
        self._indicator.post("recording")

    def on_hotkey_release(self) -> None:
        with self._lock:
            if self._state is not AppState.RECORDING:
                return
            self._state = AppState.TRANSCRIBING
        try:
            captured = self._recorder.stop()
        except Exception:
            self._set_state(AppState.READY)
            self._indicator.post("error", "Could not finish microphone recording")
            return
        self._indicator.post("transcribing")
        threading.Thread(
            target=self._process_recording, args=(captured,), daemon=True
        ).start()

    def _process_recording(self, captured: CapturedAudio) -> None:
        prepared = None
        text = None
        try:
            duration = (
                captured.samples.size / captured.sample_rate
                if captured.sample_rate > 0
                else 0.0
            )
            if duration < self._config.min_recording_seconds:
                self._indicator.post("empty")
                return
            prepared = resample_audio(
                captured.samples,
                captured.sample_rate,
                self._config.target_sample_rate,
            )
            if audio_rms(prepared) < self._config.silence_rms_threshold:
                self._indicator.post("empty")
                return
            result = self._transcriber.transcribe(prepared)
            text = result.text
            if not text:
                self._indicator.post("empty")
                return
            time.sleep(self._config.injection_delay_seconds)
            self._injector.type_text(text)
            self._indicator.post("ready")
        except Exception:
            self._indicator.post("error", "Transcription failed — please try again")
        finally:
            # Best-effort removal from process memory. Python strings are
            # immutable, so no forensic zeroisation guarantee is possible.
            if captured.samples.size:
                captured.samples.fill(0)
            if prepared is not None and prepared.size:
                prepared.fill(0)
            text = None
            if not self._stopping.is_set():
                self._set_state(AppState.READY)

    def stop(self) -> None:
        self._stopping.set()
        self._set_state(AppState.STOPPED)
        self._hotkey_listener.stop()
        if self._recorder.is_recording:
            self._recorder.cancel()
