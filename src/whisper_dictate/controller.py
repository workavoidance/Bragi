from __future__ import annotations

import enum
import threading
import time
from collections.abc import Callable

from whisper_dictate.audio import (
    AudioRecorder,
    CapturedAudio,
    MicrophoneUnavailableError,
)
from whisper_dictate.config import AppConfig
from whisper_dictate.core import audio_rms, resample_audio
from whisper_dictate.settings import LanguageMode

TRANSCRIPTION_FAILED_MESSAGE = (
    "Transcription failed. Audio was discarded; hold the key to try again."
)


class AppState(enum.Enum):
    LOADING = "loading"
    READY = "ready"
    RECORDING = "recording"
    TRANSCRIBING = "transcribing"
    CANCELLING = "cancelling"
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
        *,
        timer_factory=threading.Timer,
    ) -> None:
        self._config = config
        self._recorder = recorder
        self._transcriber = transcriber
        self._injector = injector
        self._indicator = indicator
        self._hotkey_listener = hotkey_listener
        self._state = AppState.LOADING
        self._lock = threading.Lock()
        self._workers_idle = threading.Condition(self._lock)
        self._workers: set[threading.Thread] = set()
        self._insertion_lock = threading.Lock()
        self._stopping = threading.Event()
        self._cancel_requested = threading.Event()
        self._recording_timer = None
        self._timer_factory = timer_factory

    @property
    def state(self) -> AppState:
        with self._lock:
            return self._state

    def _set_state(self, state: AppState) -> None:
        with self._lock:
            self._state = state

    def _return_to_ready_with_error(self, message: str) -> None:
        with self._lock:
            if self._stopping.is_set() or self._state is AppState.STOPPED:
                return
            self._state = AppState.READY
            self._indicator.post("error", message)

    def start(self) -> None:
        self._indicator.post("loading")
        self._hotkey_listener.start()
        self._start_worker(self._load_model)

    def _start_worker(
        self,
        target: Callable[..., None],
        *args,
        before_start: Callable[[], None] | None = None,
    ) -> bool:
        def run() -> None:
            try:
                target(*args)
            finally:
                with self._workers_idle:
                    self._workers.discard(threading.current_thread())
                    self._workers_idle.notify_all()

        worker = threading.Thread(target=run, daemon=True)
        with self._workers_idle:
            if self._stopping.is_set() or self._state is AppState.STOPPED:
                return False
            self._workers.add(worker)
            if before_start is not None:
                before_start()
            try:
                worker.start()
            except Exception:
                self._workers.discard(worker)
                self._workers_idle.notify_all()
                raise
        return True

    def _load_model(self) -> None:
        try:
            self._transcriber.load()
        except Exception:
            with self._lock:
                if self._stopping.is_set() or self._state is AppState.STOPPED:
                    return
                self._state = AppState.ERROR
            self._indicator.post(
                "model_error",
                "Speech model unavailable. Choose Retry speech model from the "
                "tray, or open Settings → Models.",
            )
            return
        with self._lock:
            if self._stopping.is_set() or self._state is AppState.STOPPED:
                return
            self._state = AppState.READY
        self._indicator.post("ready")

    def retry_model_load(self) -> bool:
        """Retry a failed startup model load without restarting Skrivi."""
        with self._lock:
            if self._stopping.is_set() or self._state is not AppState.ERROR:
                return False
            self._state = AppState.LOADING
        return self._start_worker(
            self._load_model,
            before_start=lambda: self._indicator.post(
                "loading", "Retrying local speech model…"
            ),
        )

    def on_hotkey_press(self) -> None:
        with self._lock:
            if self._stopping.is_set():
                return
            if self._state is AppState.ERROR:
                retry_model = True
            elif self._state is AppState.READY:
                retry_model = False
                self._state = AppState.RECORDING
                self._cancel_requested.clear()
            else:
                return
        if retry_model:
            self.retry_model_load()
            return
        try:
            self._recorder.start()
        except MicrophoneUnavailableError as error:
            self._return_to_ready_with_error(str(error))
            return
        except Exception:
            self._return_to_ready_with_error(
                "The microphone could not start. Check Skrivi Settings."
            )
            return
        if self._stopping.is_set():
            try:
                self._recorder.cancel()
            except Exception:
                pass
            return
        self._start_recording_timer()
        if getattr(self._recorder, "using_default_fallback", False):
            self._indicator.post(
                "recording",
                "Selected microphone unavailable. Using Windows Default "
                "temporarily. Release your dictation key, or press Esc to cancel.",
            )
        else:
            self._indicator.post("recording")

    def _start_recording_timer(self) -> None:
        if self._config.max_recording_seconds <= 0:
            return
        timer = self._timer_factory(
            self._config.max_recording_seconds,
            self._recording_limit_reached,
        )
        if hasattr(timer, "daemon"):
            timer.daemon = True
        with self._lock:
            if self._state is not AppState.RECORDING:
                return
            self._recording_timer = timer
            timer.start()

    def _cancel_recording_timer(self) -> None:
        with self._lock:
            timer = self._recording_timer
            self._recording_timer = None
        if timer is not None:
            timer.cancel()

    def _recording_limit_reached(self) -> None:
        self._cancel_current(
            "Recording cancelled after 5 minutes. Hold the key again to start over.",
            recording_only=True,
        )

    def cancel_current(self) -> None:
        """Cancel recording or prevent an in-flight transcript from being inserted."""
        self._cancel_current("Dictation cancelled")

    def _cancel_current(self, message: str, *, recording_only: bool = False) -> None:
        with self._lock:
            state = self._state
            if state is AppState.RECORDING:
                self._state = AppState.CANCELLING
                timer = self._recording_timer
                self._recording_timer = None
            elif state is AppState.TRANSCRIBING and not recording_only:
                timer = None
            else:
                return
            self._cancel_requested.set()
        if timer is not None:
            timer.cancel()
        self._indicator.post("cancelled", message)
        if state is AppState.TRANSCRIBING:
            return
        try:
            self._recorder.cancel()
        except Exception:
            self._indicator.post("error", "Could not cancel microphone recording")
        finally:
            if not self._stopping.is_set():
                self._set_state(AppState.READY)

    def on_hotkey_release(self) -> None:
        with self._lock:
            if self._state is not AppState.RECORDING:
                return
            self._state = AppState.TRANSCRIBING
            timer = self._recording_timer
            self._recording_timer = None
        if timer is not None:
            timer.cancel()
        try:
            captured = self._recorder.stop()
        except MicrophoneUnavailableError as error:
            self._return_to_ready_with_error(str(error))
            return
        except Exception:
            self._return_to_ready_with_error("Could not finish microphone recording")
            return
        started = self._start_worker(
            self._process_recording,
            captured,
            before_start=lambda: self._indicator.post("transcribing"),
        )
        if not started and captured.samples.size:
            captured.samples.fill(0)

    def _process_recording(self, captured: CapturedAudio) -> None:
        prepared = None
        text = None
        try:
            if self._cancel_requested.is_set():
                return
            duration = (
                captured.samples.size / captured.sample_rate
                if captured.sample_rate > 0
                else 0.0
            )
            if duration < self._config.min_recording_seconds:
                if (
                    getattr(self._transcriber, "language_mode", None)
                    is LanguageMode.AUTOMATIC
                ):
                    self._indicator.post(
                        "empty",
                        "Phrase too short. Automatic language detection works "
                        "better with a longer phrase.",
                    )
                else:
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
            result = self._transcriber.transcribe(
                prepared,
                cancel_event=self._cancel_requested,
            )
            if self._cancel_requested.is_set():
                return
            text = result.text
            if not text:
                self._indicator.post("empty")
                return
            time.sleep(self._config.injection_delay_seconds)
            with self._insertion_lock:
                if self._cancel_requested.is_set() or self._stopping.is_set():
                    return
                self._injector.type_text(text)
                if not self._stopping.is_set():
                    self._indicator.post("ready")
        except Exception:
            if not self._stopping.is_set():
                self._indicator.post(
                    "error",
                    TRANSCRIPTION_FAILED_MESSAGE,
                )
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

    def begin_shutdown(self) -> None:
        """Prevent new work and release active input resources."""
        self._stopping.set()
        self._cancel_requested.set()
        with self._lock:
            self._state = AppState.STOPPED
            timer = self._recording_timer
            self._recording_timer = None
        if timer is not None:
            timer.cancel()
        try:
            self._hotkey_listener.stop()
        except Exception:
            pass
        try:
            if self._recorder.is_recording:
                self._recorder.cancel()
        except Exception:
            pass
        # Once this returns, no text insertion can still be in progress or start.
        with self._insertion_lock:
            pass

    def wait_for_shutdown(self, timeout: float = 5.0) -> bool:
        """Wait briefly for cooperative model and transcription cleanup."""
        with self._workers_idle:
            return self._workers_idle.wait_for(
                lambda: not self._workers,
                timeout=max(0.0, timeout),
            )

    def stop(self, timeout: float = 5.0) -> bool:
        self.begin_shutdown()
        return self.wait_for_shutdown(timeout)
