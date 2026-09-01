from __future__ import annotations

import pytest

from whisper_dictate.lifecycle import ShutdownResult, shutdown_runtime


class FakeController:
    def __init__(self, events: list[str]) -> None:
        self.events = events

    def begin_shutdown(self) -> None:
        self.events.append("controller signalled")

    def wait_for_shutdown(self, timeout: float) -> bool:
        assert 0.0 <= timeout <= 0.5
        self.events.append("controller finished")
        return True


class FakeModelManager:
    def __init__(self, events: list[str]) -> None:
        self.events = events

    def shutdown(self, timeout: float) -> bool:
        assert 0.0 <= timeout <= 0.5
        self.events.append("models finished")
        return True


class FakeTray:
    def __init__(self, events: list[str]) -> None:
        self.events = events

    def stop(self) -> None:
        self.events.append("tray hidden")


def test_runtime_shutdown_orders_cancellation_cleanup_and_lock_release() -> None:
    events: list[str] = []

    result = shutdown_runtime(
        FakeController(events),
        FakeModelManager(events),
        FakeTray(events),
        lambda: events.append("instance lock released"),
        timeout=0.5,
    )

    assert result == ShutdownResult(True, True)
    assert events == [
        "tray hidden",
        "controller signalled",
        "models finished",
        "controller finished",
        "instance lock released",
    ]


def test_runtime_shutdown_releases_instance_lock_after_cleanup_error() -> None:
    events: list[str] = []

    class FailingManager(FakeModelManager):
        def shutdown(self, timeout: float) -> bool:
            del timeout
            raise RuntimeError("simulated cleanup failure")

    with pytest.raises(RuntimeError, match="simulated cleanup failure"):
        shutdown_runtime(
            FakeController(events),
            FailingManager(events),
            FakeTray(events),
            lambda: events.append("instance lock released"),
            timeout=0.5,
        )

    assert events[-1] == "instance lock released"
