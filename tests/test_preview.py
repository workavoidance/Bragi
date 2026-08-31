from __future__ import annotations

from whisper_dictate.preview import PREVIEW_STATES, preview_actions


class FakeIndicator:
    def __init__(self) -> None:
        self.events: list[tuple[str, str | None]] = []

    def post(self, state: str, detail: str | None = None) -> None:
        self.events.append((state, detail))


def test_every_preview_action_posts_its_own_state() -> None:
    indicator = FakeIndicator()
    actions = preview_actions(indicator)

    for label, _state, _detail in PREVIEW_STATES:
        actions[label]()

    assert indicator.events == [(state, detail) for _, state, detail in PREVIEW_STATES]
