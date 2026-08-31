from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path


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


def app_directory() -> Path:
    """Return a writable directory beside the portable executable."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]


def model_cache_directory() -> Path:
    path = app_directory() / "models"
    path.mkdir(parents=True, exist_ok=True)
    return path
