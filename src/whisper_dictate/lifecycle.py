from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass


@dataclass(frozen=True)
class ShutdownResult:
    model_operations_finished: bool
    controller_workers_finished: bool


def shutdown_runtime(
    controller,
    model_manager,
    tray,
    release_single_instance: Callable[[], None],
    *,
    timeout: float = 5.0,
) -> ShutdownResult:
    """Stop user input, finish private-data cleanup, then release the app lock."""
    deadline = time.monotonic() + max(0.0, timeout)
    try:
        tray.stop()
        controller.begin_shutdown()
        models_finished = model_manager.shutdown(max(0.0, deadline - time.monotonic()))
        workers_finished = controller.wait_for_shutdown(
            max(0.0, deadline - time.monotonic())
        )
        return ShutdownResult(models_finished, workers_finished)
    finally:
        release_single_instance()
