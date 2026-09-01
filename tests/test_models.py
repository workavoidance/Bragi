from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from pathlib import Path

import pytest

from whisper_dictate.models import (
    MODEL_MANIFEST,
    CpuSuitability,
    LocalModelManager,
    ModelFile,
    ModelIntegrityError,
    ModelInUseError,
    ModelManagerError,
    ModelSpec,
    ModelState,
    hardware_warning,
    validate_catalogue,
)

FILE_CONTENTS = {
    "config.json": b"{}\n",
    "model.bin": b"local model weights",
    "tokenizer.json": b'{"tokenizer": true}\n',
    "vocabulary.txt": "æ\nø\nå\n".encode(),
}


def checksum(content: bytes, algorithm: str) -> str:
    if algorithm == "sha256":
        return hashlib.sha256(content).hexdigest()
    header = f"blob {len(content)}\0".encode()
    return hashlib.sha1(header + content, usedforsecurity=False).hexdigest()


def small_test_spec() -> ModelSpec:
    files = tuple(
        ModelFile(
            path,
            len(content),
            checksum(content, "sha256" if path == "model.bin" else "git-sha1"),
            "sha256" if path == "model.bin" else "git-sha1",
        )
        for path, content in FILE_CONTENTS.items()
    )
    return ModelSpec(
        identifier="small",
        name="Small",
        repository="Test/small",
        revision="a" * 40,
        download_size=sum(len(content) for content in FILE_CONTENTS.values()),
        minimum_ram_gb=8,
        cpu_suitability=CpuSuitability.RECOMMENDED,
        description="Test model",
        files=files,
        recommended=True,
    )


class FakeDownloader:
    def __init__(self, *, corrupt: bool = False, fail: bool = False) -> None:
        self.corrupt = corrupt
        self.fail = fail
        self.calls: list[bool] = []

    def __call__(
        self,
        repository,
        output_dir,
        cache_dir,
        revision,
        *,
        local_files_only,
    ) -> None:
        del repository, cache_dir, revision
        self.calls.append(local_files_only)
        if local_files_only or self.fail:
            raise FileNotFoundError("not cached")
        for name, content in FILE_CONTENTS.items():
            if self.corrupt and name == "model.bin":
                content = b"damaged model weights"
            (output_dir / name).write_bytes(content)


class CachedDownloader(FakeDownloader):
    def __call__(self, *args, local_files_only, **kwargs) -> None:
        del args
        assert local_files_only is True
        self.calls.append(local_files_only)
        output_dir = kwargs["output_dir"]
        for name, content in FILE_CONTENTS.items():
            (output_dir / name).write_bytes(content)


def test_catalogue_requires_small_as_the_single_recommended_model() -> None:
    spec = small_test_spec()

    assert validate_catalogue([spec]) == (spec,)
    with pytest.raises(ValueError, match="single recommended"):
        validate_catalogue([replace(spec, recommended=False)])


def test_download_is_verified_then_installed_atomically(tmp_path: Path) -> None:
    downloader = FakeDownloader()
    manager = LocalModelManager(
        tmp_path / "models", catalogue=[small_test_spec()], downloader=downloader
    )
    events = []

    installed = manager.install("small", events.append)

    assert downloader.calls == [True, False]
    assert installed == tmp_path / "models" / "installed" / "small"
    assert manager.is_installed("small") is True
    assert json.loads((installed / MODEL_MANIFEST).read_text())["model"] == "small"
    assert [event.state for event in events] == [
        ModelState.DOWNLOADING,
        ModelState.VERIFYING,
        ModelState.INSTALLED,
    ]
    assert list(manager.staging_root.iterdir()) == []


def test_existing_download_cache_is_reused_without_network(tmp_path: Path) -> None:
    downloader = CachedDownloader()
    manager = LocalModelManager(
        tmp_path / "models", catalogue=[small_test_spec()], downloader=downloader
    )

    manager.install("small")
    identifier, path = manager.resolve_startup_model("small")

    assert downloader.calls == [True]
    assert identifier == "small"
    assert path == manager.model_path("small")


def test_interrupted_or_corrupt_download_is_never_installed(tmp_path: Path) -> None:
    failed = LocalModelManager(
        tmp_path / "failed",
        catalogue=[small_test_spec()],
        downloader=FakeDownloader(fail=True),
    )
    corrupt = LocalModelManager(
        tmp_path / "corrupt",
        catalogue=[small_test_spec()],
        downloader=FakeDownloader(corrupt=True),
    )

    with pytest.raises(ModelManagerError, match="could not be downloaded"):
        failed.install("small")
    with pytest.raises(ModelIntegrityError, match="integrity"):
        corrupt.install("small")

    assert failed.is_installed("small") is False
    assert corrupt.is_installed("small") is False
    assert list(failed.staging_root.iterdir()) == []
    assert list(corrupt.staging_root.iterdir()) == []


def test_stale_partial_downloads_are_removed_on_startup(tmp_path: Path) -> None:
    partial = tmp_path / "models" / ".downloads" / "small-interrupted"
    partial.mkdir(parents=True)
    (partial / "model.bin").write_bytes(b"private partial bytes")

    LocalModelManager(tmp_path / "models", catalogue=[small_test_spec()])

    assert partial.exists() is False


def test_verified_model_folder_can_be_imported_without_internet(tmp_path: Path) -> None:
    source_manager = LocalModelManager(
        tmp_path / "source",
        catalogue=[small_test_spec()],
        downloader=FakeDownloader(),
    )
    source = source_manager.install("small")
    destination_manager = LocalModelManager(
        tmp_path / "destination",
        catalogue=[small_test_spec()],
        downloader=FakeDownloader(fail=True),
    )

    imported = destination_manager.import_directory(source)

    assert imported.name == "small"
    assert destination_manager.verify_installed("small").is_dir()


def test_tampered_import_is_rejected_and_active_model_cannot_be_removed(
    tmp_path: Path,
) -> None:
    manager = LocalModelManager(
        tmp_path / "models",
        catalogue=[small_test_spec()],
        downloader=FakeDownloader(),
    )
    source = manager.install("small")
    (source / "model.bin").write_bytes(b"tampered model weights")

    with pytest.raises(ModelIntegrityError, match="integrity"):
        manager.verify_installed("small")
    with pytest.raises(ModelInUseError, match="currently active"):
        manager.remove("small", active_model="small")


def test_hardware_warning_is_actionable() -> None:
    spec = replace(
        small_test_spec(),
        name="Medium",
        minimum_ram_gb=16,
        cpu_suitability=CpuSuitability.SLOW,
    )

    assert "reports 8.0 GB" in hardware_warning(spec, 8.0)
    assert "likely to transcribe slowly" in hardware_warning(spec, 32.0)
