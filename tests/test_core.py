from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pytest

from whisper_dictate.core import audio_rms, join_segments, mono_float32, resample_audio


@dataclass
class Segment:
    text: str


def test_stereo_is_mixed_to_mono() -> None:
    stereo = np.array([[1.0, -1.0], [0.5, 0.5]], dtype=np.float32)
    result = mono_float32(stereo)
    np.testing.assert_allclose(result, [0.0, 0.5])
    assert result.dtype == np.float32


def test_resample_preserves_duration_and_endpoints() -> None:
    audio = np.linspace(-1.0, 1.0, 48_000, dtype=np.float32)
    result = resample_audio(audio, 48_000, 16_000)
    assert result.size == 16_000
    assert result[0] == pytest.approx(-1.0)
    assert result[-1] == pytest.approx(1.0)


def test_resample_rejects_invalid_rates() -> None:
    with pytest.raises(ValueError):
        resample_audio(np.ones(10), 0, 16_000)


def test_audio_rms() -> None:
    assert audio_rms(np.zeros(100, dtype=np.float32)) == 0.0
    assert audio_rms(np.ones(100, dtype=np.float32)) == pytest.approx(1.0)


def test_join_segments_does_not_rewrite_content() -> None:
    segments = [Segment(" Hello,"), Segment(" um, world."), Segment("  ")]
    assert join_segments(segments) == "Hello, um, world."
