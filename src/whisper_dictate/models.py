from __future__ import annotations

import ctypes
import hashlib
import json
import os
import shutil
import tempfile
import threading
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

MODEL_MANIFEST = "bragi-model.json"
MODEL_SCHEMA_VERSION = 1
MEMORY_ERRORS = (AttributeError, OSError, ValueError)
MANIFEST_ERRORS = (OSError, ValueError, TypeError)


class CpuSuitability(StrEnum):
    FASTEST = "fastest"
    FASTER = "faster"
    RECOMMENDED = "recommended"
    SLOW = "slow"


class ModelState(StrEnum):
    NOT_INSTALLED = "not_installed"
    DOWNLOADING = "downloading"
    VERIFYING = "verifying"
    INSTALLED = "installed"
    LOADING = "loading"
    ERROR = "error"


@dataclass(frozen=True)
class ModelFile:
    path: str
    size: int
    checksum: str
    algorithm: str


@dataclass(frozen=True)
class ModelSpec:
    identifier: str
    name: str
    repository: str
    revision: str
    download_size: int
    minimum_ram_gb: int
    cpu_suitability: CpuSuitability
    description: str
    files: tuple[ModelFile, ...]
    recommended: bool = False

    @property
    def download_size_label(self) -> str:
        if self.download_size >= 1_000_000_000:
            return f"{self.download_size / 1_000_000_000:.2f} GB"
        return f"{round(self.download_size / 1_000_000)} MB"


@dataclass(frozen=True)
class ModelStatus:
    identifier: str
    state: ModelState
    progress: float | None = None
    detail: str = ""


class ModelManagerError(RuntimeError):
    """Base error for safe local model operations."""


class ModelCatalogueError(ValueError):
    """Raised when the packaged model catalogue is invalid."""


class ModelBusyError(ModelManagerError):
    """Raised when a second model operation is requested concurrently."""


class ModelNotInstalledError(ModelManagerError):
    """Raised when an operation needs a complete local model."""


class ModelIntegrityError(ModelManagerError):
    """Raised when files do not match the pinned catalogue."""


class ModelInUseError(ModelManagerError):
    """Raised when removal would break the active transcription model."""


def _files(
    config_size: int, config_oid: str, model_size: int, model_sha256: str
) -> tuple[ModelFile, ...]:
    return (
        ModelFile("config.json", config_size, config_oid, "git-sha1"),
        ModelFile("model.bin", model_size, model_sha256, "sha256"),
        ModelFile(
            "tokenizer.json",
            2_203_239,
            "7818adb6de9fa3064d3ff81226fdd675be1f6344",
            "git-sha1",
        ),
        ModelFile(
            "vocabulary.txt",
            459_861,
            "c9074644d9d1205686f16d411564729461324b75",
            "git-sha1",
        ),
    )


MODEL_CATALOGUE = (
    ModelSpec(
        identifier="tiny",
        name="Tiny",
        repository="Systran/faster-whisper-tiny",
        revision="d90ca5fe260221311c53c58e660288d3deb8d356",
        download_size=78_203_619,
        minimum_ram_gb=4,
        cpu_suitability=CpuSuitability.FASTEST,
        description="Fastest response, with the lowest transcription accuracy.",
        files=_files(
            2_249,
            "3baa18e2b321a2f489614607852a729fcd516480",
            75_538_270,
            "dcb76c6586fc06cbdac6dd21f14cfd129cc4cdd9dce19bf4ffa62e59cbe6e6d1",
        ),
    ),
    ModelSpec(
        identifier="base",
        name="Base",
        repository="Systran/faster-whisper-base",
        revision="ebe41f70d5b6dfa9166e2c581c45c9c0cfc57b66",
        download_size=147_882_941,
        minimum_ram_gb=4,
        cpu_suitability=CpuSuitability.FASTER,
        description="Faster on a CPU, with lower accuracy than Small.",
        files=_files(
            2_309,
            "867cf1a0fece1394e01d55e287ba2f09a577c046",
            145_217_532,
            "d01c3014881c9c6f3133c182f3d2887eb6ca1c789a7538c5c007196857a0a6a9",
        ),
    ),
    ModelSpec(
        identifier="small",
        name="Small",
        repository="Systran/faster-whisper-small",
        revision="536b0662742c02347bc0e980a01041f333bce120",
        download_size=486_212_372,
        minimum_ram_gb=8,
        cpu_suitability=CpuSuitability.RECOMMENDED,
        description="Recommended balance of Norwegian accuracy and CPU speed.",
        files=_files(
            2_370,
            "e5047537059bd8f182d9ca64c470201585015187",
            483_546_902,
            "3e305921506d8872816023e4c273e75d2419fb89b24da97b4fe7bce14170d671",
        ),
        recommended=True,
    ),
    ModelSpec(
        identifier="medium",
        name="Medium",
        repository="Systran/faster-whisper-medium",
        revision="08e178d48790749d25932bbc082711ddcfdfbc4f",
        download_size=1_530_571_735,
        minimum_ram_gb=16,
        cpu_suitability=CpuSuitability.SLOW,
        description="Potentially more accurate, but often impractical on a CPU.",
        files=_files(
            2_257,
            "242aa06a480a7b5509375c645097e87af5136774",
            1_527_906_378,
            "9b45e1009dcc4ab601eff815b61d80e60ce3fd8c74c1a14f4a282258286b51ae",
        ),
    ),
)


def validate_catalogue(catalogue: Iterable[ModelSpec]) -> tuple[ModelSpec, ...]:
    result = tuple(catalogue)
    identifiers = [model.identifier for model in result]
    if not result or len(set(identifiers)) != len(identifiers):
        raise ModelCatalogueError("Model identifiers must be present and unique")
    recommended = [model for model in result if model.recommended]
    if len(recommended) != 1 or recommended[0].identifier != "small":
        raise ModelCatalogueError("Small must be the single recommended model")
    for model in result:
        if (
            not model.identifier.isascii()
            or not model.identifier.replace("-", "").isalnum()
            or "/" not in model.repository
            or len(model.revision) != 40
            or any(character not in "0123456789abcdef" for character in model.revision)
            or model.download_size <= 0
            or model.minimum_ram_gb <= 0
        ):
            raise ModelCatalogueError(f"Model {model.identifier!r} is invalid")
        paths = [file.path for file in model.files]
        if set(paths) != {
            "config.json",
            "model.bin",
            "tokenizer.json",
            "vocabulary.txt",
        }:
            raise ModelCatalogueError(
                f"Model {model.identifier!r} has an invalid file manifest"
            )
        for file in model.files:
            if file.size <= 0 or file.algorithm not in {"sha256", "git-sha1"}:
                raise ModelCatalogueError(
                    f"Model {model.identifier!r} has an invalid checksum"
                )
            expected_length = 64 if file.algorithm == "sha256" else 40
            if len(file.checksum) != expected_length:
                raise ModelCatalogueError(
                    f"Model {model.identifier!r} has an invalid checksum"
                )
    return result


VALIDATED_CATALOGUE = validate_catalogue(MODEL_CATALOGUE)
MODEL_BY_ID = {model.identifier: model for model in VALIDATED_CATALOGUE}


def total_physical_memory_gb() -> float | None:
    if os.name == "nt":

        class MemoryStatus(ctypes.Structure):
            _fields_ = [
                ("length", ctypes.c_ulong),
                ("memory_load", ctypes.c_ulong),
                ("total_physical", ctypes.c_ulonglong),
                ("available_physical", ctypes.c_ulonglong),
                ("total_page_file", ctypes.c_ulonglong),
                ("available_page_file", ctypes.c_ulonglong),
                ("total_virtual", ctypes.c_ulonglong),
                ("available_virtual", ctypes.c_ulonglong),
                ("available_extended_virtual", ctypes.c_ulonglong),
            ]

        status = MemoryStatus()
        status.length = ctypes.sizeof(status)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
            return status.total_physical / (1024**3)
        return None
    try:
        pages = os.sysconf("SC_PHYS_PAGES")
        page_size = os.sysconf("SC_PAGE_SIZE")
        return pages * page_size / (1024**3)
    except MEMORY_ERRORS:
        return None


def hardware_warning(model: ModelSpec, memory_gb: float | None) -> str | None:
    # Windows can report slightly less than the marketed RAM capacity.
    if memory_gb is not None and memory_gb + 0.5 < model.minimum_ram_gb:
        return (
            f"{model.name} is intended for PCs with at least "
            f"{model.minimum_ram_gb} GB of RAM. This PC reports "
            f"{memory_gb:.1f} GB."
        )
    if model.cpu_suitability is CpuSuitability.SLOW:
        return (
            f"{model.name} is likely to transcribe slowly on a CPU. "
            "Small is the recommended model for typical PCs."
        )
    return None


def _default_downloader(
    repository: str,
    output_dir: Path,
    cache_dir: Path,
    revision: str,
    *,
    local_files_only: bool,
):
    from faster_whisper.utils import download_model

    return download_model(
        repository,
        output_dir=str(output_dir),
        cache_dir=str(cache_dir),
        revision=revision,
        local_files_only=local_files_only,
    )


def _file_checksum(path: Path, algorithm: str) -> str:
    if algorithm == "sha256":
        digest = hashlib.sha256()
        prefix = b""
    elif algorithm == "git-sha1":
        digest = hashlib.sha1(usedforsecurity=False)
        prefix = f"blob {path.stat().st_size}\0".encode()
    else:
        raise ValueError("Unsupported model checksum algorithm")
    digest.update(prefix)
    with path.open("rb") as file:
        while block := file.read(1024 * 1024):
            digest.update(block)
    return digest.hexdigest()


class LocalModelManager:
    """Install pinned faster-whisper models without exposing partial state."""

    def __init__(
        self,
        root: Path,
        *,
        catalogue: Iterable[ModelSpec] = VALIDATED_CATALOGUE,
        downloader=None,
    ) -> None:
        self.root = root
        self.catalogue = validate_catalogue(catalogue)
        self._by_id = {model.identifier: model for model in self.catalogue}
        self._downloader = downloader or _default_downloader
        self._lock = threading.Lock()
        self._active_operation: str | None = None
        self._live_status: dict[str, ModelStatus] = {}
        self._clean_stale_downloads()

    @property
    def installed_root(self) -> Path:
        return self.root / "installed"

    @property
    def download_cache(self) -> Path:
        # Keep using the prototype's cache root so an existing Small download
        # can be reused during migration into Bragi's verified installed area.
        return self.root

    @property
    def staging_root(self) -> Path:
        return self.root / ".downloads"

    def spec(self, identifier: str) -> ModelSpec:
        try:
            return self._by_id[identifier]
        except KeyError:
            raise ModelManagerError("That model is not in Bragi's catalogue.") from None

    def model_path(self, identifier: str) -> Path:
        return self.installed_root / self.spec(identifier).identifier

    def _clean_stale_downloads(self) -> None:
        if not self.staging_root.is_dir():
            return
        for child in self.staging_root.iterdir():
            if child.is_dir():
                shutil.rmtree(child, ignore_errors=True)

    def _manifest_document(self, spec: ModelSpec) -> dict[str, object]:
        return {
            "schema_version": MODEL_SCHEMA_VERSION,
            "model": spec.identifier,
            "repository": spec.repository,
            "revision": spec.revision,
            "files": [
                {
                    "path": file.path,
                    "size": file.size,
                    "algorithm": file.algorithm,
                    "checksum": file.checksum,
                }
                for file in spec.files
            ],
        }

    def _manifest_matches(self, directory: Path, spec: ModelSpec) -> bool:
        try:
            document = json.loads(
                (directory / MODEL_MANIFEST).read_text(encoding="utf-8")
            )
        except MANIFEST_ERRORS:
            return False
        return document == self._manifest_document(spec)

    def verify_directory(
        self, directory: Path, spec: ModelSpec, *, thorough: bool
    ) -> None:
        for expected in spec.files:
            path = directory / expected.path
            try:
                size = path.stat().st_size
            except OSError as error:
                raise ModelIntegrityError(
                    f"{spec.name} is incomplete. Download or import it again."
                ) from error
            if expected.size and size != expected.size:
                raise ModelIntegrityError(
                    f"{spec.name} did not pass integrity verification. "
                    "Download or import it again."
                )
            if (
                thorough
                and _file_checksum(path, expected.algorithm) != expected.checksum
            ):
                raise ModelIntegrityError(
                    f"{spec.name} did not pass integrity verification. "
                    "Download or import it again."
                )

    def is_installed(self, identifier: str) -> bool:
        spec = self.spec(identifier)
        path = self.model_path(identifier)
        if not self._manifest_matches(path, spec):
            return False
        try:
            self.verify_directory(path, spec, thorough=False)
        except ModelIntegrityError:
            return False
        return True

    def verify_installed(self, identifier: str, *, thorough: bool = True) -> Path:
        spec = self.spec(identifier)
        path = self.model_path(identifier)
        if not self._manifest_matches(path, spec):
            raise ModelNotInstalledError(
                f"{spec.name} is not completely installed on this PC."
            )
        self.verify_directory(path, spec, thorough=thorough)
        return path

    def resolve_startup_model(
        self,
        requested: str,
        callback: Callable[[ModelStatus], None] | None = None,
    ) -> tuple[str, Path]:
        """Resolve an installed local path, downloading only the default setup model."""
        if self.is_installed(requested):
            return requested, self.model_path(requested)
        if requested != "small" and self.is_installed("small"):
            return "small", self.model_path("small")
        return "small", self.install("small", callback)

    def status(self, identifier: str) -> ModelStatus:
        self.spec(identifier)
        with self._lock:
            live = self._live_status.get(identifier)
        if live is not None:
            return live
        state = (
            ModelState.INSTALLED
            if self.is_installed(identifier)
            else ModelState.NOT_INSTALLED
        )
        return ModelStatus(identifier, state)

    def statuses(self) -> tuple[ModelStatus, ...]:
        return tuple(self.status(spec.identifier) for spec in self.catalogue)

    def _set_status(
        self,
        identifier: str,
        state: ModelState,
        detail: str,
        callback: Callable[[ModelStatus], None] | None,
        progress: float | None = None,
    ) -> None:
        status = ModelStatus(identifier, state, progress, detail)
        with self._lock:
            if state in {ModelState.INSTALLED, ModelState.NOT_INSTALLED}:
                self._live_status.pop(identifier, None)
            else:
                self._live_status[identifier] = status
        if callback is not None:
            try:
                callback(status)
            except Exception:
                # An observer cannot be allowed to corrupt an install transaction.
                pass

    def _begin(self, identifier: str) -> None:
        with self._lock:
            if self._active_operation is not None:
                raise ModelBusyError(
                    "Finish the current model operation before starting another."
                )
            self._active_operation = identifier

    def _finish(self) -> None:
        with self._lock:
            self._active_operation = None

    def _write_manifest(self, directory: Path, spec: ModelSpec) -> None:
        payload = json.dumps(
            self._manifest_document(spec), ensure_ascii=False, indent=2
        )
        (directory / MODEL_MANIFEST).write_text(payload + "\n", encoding="utf-8")

    def _install_staging(self, staging: Path, spec: ModelSpec) -> Path:
        self.verify_directory(staging, spec, thorough=True)
        cache_metadata = staging / ".cache"
        if cache_metadata.is_dir():
            shutil.rmtree(cache_metadata, ignore_errors=True)
        self._write_manifest(staging, spec)
        destination = self.model_path(spec.identifier)
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.exists():
            quarantine = Path(
                tempfile.mkdtemp(
                    prefix=f"{spec.identifier}-old-", dir=destination.parent
                )
            )
            quarantine.rmdir()
            os.replace(destination, quarantine)
            try:
                os.replace(staging, destination)
            except Exception:
                os.replace(quarantine, destination)
                raise
            shutil.rmtree(quarantine, ignore_errors=True)
        else:
            os.replace(staging, destination)
        return destination

    def install(
        self,
        identifier: str,
        callback: Callable[[ModelStatus], None] | None = None,
    ) -> Path:
        spec = self.spec(identifier)
        if self.is_installed(identifier):
            return self.model_path(identifier)
        self._begin(identifier)
        self.staging_root.mkdir(parents=True, exist_ok=True)
        staging = Path(tempfile.mkdtemp(prefix=f"{identifier}-", dir=self.staging_root))
        try:
            self._set_status(
                identifier,
                ModelState.DOWNLOADING,
                f"Downloading {spec.name} from the internet…",
                callback,
            )
            try:
                self._downloader(
                    spec.repository,
                    output_dir=staging,
                    cache_dir=self.download_cache,
                    revision=spec.revision,
                    local_files_only=True,
                )
            except Exception:
                shutil.rmtree(staging, ignore_errors=True)
                staging.mkdir(parents=True)
                self._downloader(
                    spec.repository,
                    output_dir=staging,
                    cache_dir=self.download_cache,
                    revision=spec.revision,
                    local_files_only=False,
                )
            self._set_status(
                identifier,
                ModelState.VERIFYING,
                f"Verifying {spec.name}…",
                callback,
                0.95,
            )
            destination = self._install_staging(staging, spec)
            self._set_status(
                identifier,
                ModelState.INSTALLED,
                f"{spec.name} is installed.",
                callback,
                1.0,
            )
            return destination
        except Exception as error:
            shutil.rmtree(staging, ignore_errors=True)
            self._set_status(
                identifier,
                ModelState.ERROR,
                f"{spec.name} could not be installed safely.",
                callback,
            )
            if isinstance(error, ModelManagerError):
                raise
            raise ModelManagerError(
                f"{spec.name} could not be downloaded. Check the internet "
                "connection and try again."
            ) from error
        finally:
            self._finish()

    def import_directory(
        self,
        source: Path,
        callback: Callable[[ModelStatus], None] | None = None,
    ) -> Path:
        try:
            manifest = json.loads((source / MODEL_MANIFEST).read_text(encoding="utf-8"))
            identifier = manifest["model"]
        except (OSError, ValueError, KeyError, TypeError) as error:
            raise ModelIntegrityError(
                "That folder is not a complete Bragi model export."
            ) from error
        spec = self.spec(identifier)
        if manifest != self._manifest_document(spec):
            raise ModelIntegrityError(
                "That model does not match Bragi's trusted catalogue."
            )
        self._begin(identifier)
        self.staging_root.mkdir(parents=True, exist_ok=True)
        staging = Path(
            tempfile.mkdtemp(prefix=f"{identifier}-import-", dir=self.staging_root)
        )
        try:
            self._set_status(
                identifier,
                ModelState.VERIFYING,
                f"Checking imported {spec.name} files…",
                callback,
            )
            for expected in spec.files:
                shutil.copy2(source / expected.path, staging / expected.path)
            destination = self._install_staging(staging, spec)
            self._set_status(
                identifier,
                ModelState.INSTALLED,
                f"{spec.name} was imported.",
                callback,
                1.0,
            )
            return destination
        except Exception as error:
            shutil.rmtree(staging, ignore_errors=True)
            self._set_status(
                identifier,
                ModelState.ERROR,
                f"{spec.name} could not be imported safely.",
                callback,
            )
            if isinstance(error, ModelManagerError):
                raise
            raise ModelIntegrityError(
                "The imported model is incomplete or damaged."
            ) from error
        finally:
            self._finish()

    def remove(self, identifier: str, *, active_model: str | None) -> None:
        spec = self.spec(identifier)
        if identifier == active_model:
            raise ModelInUseError(
                f"{spec.name} is currently active. Select another model first."
            )
        self._begin(identifier)
        try:
            destination = self.model_path(identifier)
            if destination.exists():
                shutil.rmtree(destination)
            self._set_status(
                identifier,
                ModelState.NOT_INSTALLED,
                f"{spec.name} was removed.",
                None,
            )
        finally:
            self._finish()
