from __future__ import annotations

from collections.abc import Iterable
from typing import Protocol

import numpy as np


class SegmentLike(Protocol):
    text: str


def mono_float32(audio: np.ndarray) -> np.ndarray:
    """Return contiguous, mono float32 audio without changing its duration."""
    data = np.asarray(audio, dtype=np.float32)
    if data.ndim == 0:
        return np.empty(0, dtype=np.float32)
    if data.ndim == 2:
        data = data.mean(axis=1)
    elif data.ndim != 1:
        raise ValueError("Audio must have one or two dimensions")
    return np.ascontiguousarray(data, dtype=np.float32)


def resample_audio(
    audio: np.ndarray, source_rate: int, target_rate: int = 16_000
) -> np.ndarray:
    """Linearly resample mono speech audio using only NumPy."""
    data = mono_float32(audio)
    if source_rate <= 0 or target_rate <= 0:
        raise ValueError("Sample rates must be positive")
    if data.size == 0 or source_rate == target_rate:
        return data.copy()

    target_length = max(1, round(data.size * target_rate / source_rate))
    source_positions = np.arange(data.size, dtype=np.float64)
    target_positions = np.linspace(
        0, data.size - 1, num=target_length, dtype=np.float64
    )
    result = np.interp(target_positions, source_positions, data)
    return np.ascontiguousarray(result, dtype=np.float32)


def audio_rms(audio: np.ndarray) -> float:
    data = mono_float32(audio)
    if data.size == 0:
        return 0.0
    return float(np.sqrt(np.mean(np.square(data, dtype=np.float64))))


def join_segments(segments: Iterable[SegmentLike]) -> str:
    """Join Whisper's segments without editorial rewriting."""
    return "".join(segment.text for segment in segments).strip()
