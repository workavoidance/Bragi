from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AppConfig:
    model_name: str = "small"
    device: str = "cpu"
    compute_type: str = "int8"
    target_sample_rate: int = 16_000
    beam_size: int = 5
    min_recording_seconds: float = 0.25
    silence_rms_threshold: float = 0.0015
    injection_delay_seconds: float = 0.08
