from __future__ import annotations

import threading
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from whisper_dictate.config import AppConfig
from whisper_dictate.core import join_segments
from whisper_dictate.settings import LanguageMode


@dataclass(frozen=True)
class Transcription:
    text: str
    detected_language: str | None
    language_probability: float | None


@dataclass(frozen=True)
class LoadedModelSnapshot:
    identifier: str
    model: object


def language_options(mode: LanguageMode) -> tuple[str | None, bool]:
    if mode is LanguageMode.ENGLISH:
        return "en", False
    if mode is LanguageMode.NORWEGIAN:
        return "no", False
    if mode is LanguageMode.MULTILINGUAL:
        return None, True
    return None, False


class LocalWhisperTranscriber:
    def __init__(
        self,
        config: AppConfig,
        model_cache: Path,
        language: LanguageMode = LanguageMode.AUTOMATIC,
        model_name: str | None = None,
        model_resolver: Callable[[str], tuple[str, str | Path]] | None = None,
    ) -> None:
        self._config = config
        self._model_cache = model_cache
        self._model = None
        self._model_name = model_name or config.model_name
        self._active_model_name = self._model_name
        self._model_resolver = model_resolver
        self._language = language
        self._settings_lock = threading.Lock()
        self._model_lock = threading.Lock()

    @property
    def language_mode(self) -> LanguageMode:
        with self._settings_lock:
            return self._language

    def set_language_mode(self, mode: LanguageMode) -> None:
        with self._settings_lock:
            self._language = mode

    @property
    def active_model(self) -> str:
        with self._model_lock:
            return self._active_model_name

    def _create_model(self, source: str | Path):
        from faster_whisper import WhisperModel

        return WhisperModel(
            str(source),
            device=self._config.device,
            compute_type=self._config.compute_type,
            download_root=str(self._model_cache),
        )

    def load(self) -> None:
        with self._model_lock:
            if self._model is not None:
                return
            requested = self._model_name
        if self._model_resolver is None:
            identifier, source = requested, requested
        else:
            identifier, source = self._model_resolver(requested)
        candidate = self._create_model(source)
        with self._model_lock:
            if self._model is None:
                self._model = candidate
                self._active_model_name = identifier

    def switch_model(self, identifier: str, source: str | Path) -> LoadedModelSnapshot:
        """Load a candidate completely before replacing the working model."""
        candidate = self._create_model(source)
        with self._model_lock:
            if self._model is None:
                raise RuntimeError("The current model has not finished loading")
            previous = LoadedModelSnapshot(self._active_model_name, self._model)
            self._model = candidate
            self._active_model_name = identifier
            self._model_name = identifier
        return previous

    def restore_model(self, snapshot: LoadedModelSnapshot) -> None:
        with self._model_lock:
            self._model = snapshot.model
            self._active_model_name = snapshot.identifier
            self._model_name = snapshot.identifier

    def transcribe(self, audio_16khz: np.ndarray) -> Transcription:
        self.load()
        with self._settings_lock:
            mode = self._language
        language, multilingual = language_options(mode)
        with self._model_lock:
            model = self._model
        segments, info = model.transcribe(
            audio_16khz,
            language=language,
            beam_size=self._config.beam_size,
            temperature=0.0,
            condition_on_previous_text=False,
            vad_filter=False,
            word_timestamps=False,
            multilingual=multilingual,
        )
        text = join_segments(segments)
        return Transcription(
            text=text,
            detected_language=getattr(info, "language", None),
            language_probability=getattr(info, "language_probability", None),
        )
