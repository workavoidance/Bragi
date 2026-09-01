from __future__ import annotations

import threading
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
    ) -> None:
        self._config = config
        self._model_cache = model_cache
        self._model = None
        self._language = language
        self._settings_lock = threading.Lock()

    @property
    def language_mode(self) -> LanguageMode:
        with self._settings_lock:
            return self._language

    def set_language_mode(self, mode: LanguageMode) -> None:
        with self._settings_lock:
            self._language = mode

    def load(self) -> None:
        if self._model is not None:
            return
        from faster_whisper import WhisperModel

        self._model = WhisperModel(
            self._config.model_name,
            device=self._config.device,
            compute_type=self._config.compute_type,
            download_root=str(self._model_cache),
        )

    def transcribe(self, audio_16khz: np.ndarray) -> Transcription:
        self.load()
        with self._settings_lock:
            mode = self._language
        language, multilingual = language_options(mode)
        segments, info = self._model.transcribe(
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
