from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from whisper_dictate.config import AppConfig
from whisper_dictate.core import join_segments


@dataclass(frozen=True)
class Transcription:
    text: str
    detected_language: str | None
    language_probability: float | None


class LocalWhisperTranscriber:
    def __init__(self, config: AppConfig, model_cache: Path) -> None:
        self._config = config
        self._model_cache = model_cache
        self._model = None

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
        segments, info = self._model.transcribe(
            audio_16khz,
            language=None,
            beam_size=self._config.beam_size,
            temperature=0.0,
            condition_on_previous_text=False,
            vad_filter=False,
            word_timestamps=False,
            multilingual=True,
        )
        text = join_segments(segments)
        return Transcription(
            text=text,
            detected_language=getattr(info, "language", None),
            language_probability=getattr(info, "language_probability", None),
        )
