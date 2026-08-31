from __future__ import annotations

from tools.dev_runner import application_command, source_changed, source_snapshot


def test_preview_command_uses_development_and_preview_flags() -> None:
    assert application_command("preview", "python.exe") == [
        "python.exe",
        "-m",
        "whisper_dictate",
        "--development",
        "--preview",
    ]


def test_real_command_does_not_enable_preview() -> None:
    command = application_command("real", "python.exe")

    assert command[-1] == "--development"
    assert "--preview" not in command


def test_source_snapshot_detects_changes(tmp_path) -> None:
    source = tmp_path / "src"
    source.mkdir()
    module = source / "module.py"
    module.write_text("VALUE = 1\n", encoding="utf-8")
    previous = source_snapshot(source)

    module.write_text("VALUE = 200\n", encoding="utf-8")
    current = source_snapshot(source)

    assert source_changed(previous, current)


def test_source_snapshot_ignores_non_python_files(tmp_path) -> None:
    source = tmp_path / "src"
    source.mkdir()
    (source / "notes.txt").write_text("first", encoding="utf-8")
    previous = source_snapshot(source)

    (source / "notes.txt").write_text("second", encoding="utf-8")
    current = source_snapshot(source)

    assert not source_changed(previous, current)
