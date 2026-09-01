from __future__ import annotations

import threading
from collections.abc import Callable
from pathlib import Path

from PySide6.QtCore import QObject, Signal, Slot
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from whisper_dictate.model_runtime import ModelActivationError, ModelRuntime
from whisper_dictate.models import (
    VALIDATED_CATALOGUE,
    LocalModelManager,
    ModelManagerError,
    ModelOperationCancelled,
    ModelState,
    ModelStatus,
    hardware_warning,
    total_physical_memory_gb,
)
from whisper_dictate.settings import SettingsWriteError


class _TaskSignals(QObject):
    status = Signal(object)
    succeeded = Signal(str)
    failed = Signal(str)
    cancelled = Signal(str)


class ModelManagerPanel(QWidget):
    """Accessible model installation and activation controls."""

    model_activated = Signal(str)

    def __init__(
        self,
        manager: LocalModelManager | None,
        runtime: ModelRuntime | None,
        parent: QWidget | None = None,
        *,
        memory_gb: float | None = None,
    ) -> None:
        super().__init__(parent)
        self._manager = manager
        self._runtime = runtime
        self._catalogue = manager.catalogue if manager else VALIDATED_CATALOGUE
        self._memory_gb = total_physical_memory_gb() if memory_gb is None else memory_gb
        self._task_signals: _TaskSignals | None = None
        self._manager_signals = _TaskSignals(self)
        self._manager_signals.status.connect(self._status_changed)
        if manager is not None:
            manager.add_status_listener(self._manager_signals.status.emit)
        self.setAccessibleName("Local speech models")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 14, 12, 12)
        layout.setSpacing(12)

        introduction = QLabel(
            "Speech models are installed on this PC. Downloading a new model "
            "uses the internet only when you request it. Installed models work "
            "without an internet connection.",
            self,
        )
        introduction.setWordWrap(True)
        introduction.setAccessibleName("Model privacy and download explanation")
        layout.addWidget(introduction)

        self.model_combo = QComboBox(self)
        self.model_combo.setAccessibleName("Speech model")
        for spec in self._catalogue:
            label = f"{spec.name} (recommended)" if spec.recommended else spec.name
            self.model_combo.addItem(label, spec.identifier)
        self.model_combo.currentIndexChanged.connect(self.refresh)
        layout.addWidget(self.model_combo)

        self.details = QLabel(self)
        self.details.setWordWrap(True)
        self.details.setAccessibleName("Selected model details")
        layout.addWidget(self.details)

        self.state = QLabel(self)
        self.state.setWordWrap(True)
        self.state.setAccessibleName("Selected model status")
        layout.addWidget(self.state)

        self.progress = QProgressBar(self)
        self.progress.setAccessibleName("Model operation progress")
        self.progress.setTextVisible(True)
        self.progress.hide()
        layout.addWidget(self.progress)

        button_row = QHBoxLayout()
        self.download_button = QPushButton("&Download", self)
        self.download_button.setAccessibleName("Download selected model")
        self.activate_button = QPushButton("&Use model", self)
        self.activate_button.setAccessibleName("Use selected speech model")
        self.remove_button = QPushButton("&Remove", self)
        self.remove_button.setAccessibleName("Remove selected model")
        self.import_button = QPushButton("&Import folder…", self)
        self.import_button.setAccessibleName("Import a Bragi model folder")
        self.cancel_button = QPushButton("&Cancel download", self)
        self.cancel_button.setAccessibleName("Cancel model download")
        self.cancel_button.hide()
        button_row.addWidget(self.download_button)
        button_row.addWidget(self.activate_button)
        button_row.addWidget(self.remove_button)
        button_row.addWidget(self.import_button)
        button_row.addWidget(self.cancel_button)
        layout.addLayout(button_row)

        self.download_button.clicked.connect(self._download)
        self.activate_button.clicked.connect(self._activate)
        self.remove_button.clicked.connect(self._remove)
        self.import_button.clicked.connect(self._import)
        self.cancel_button.clicked.connect(self.cancel_active_operation)

        if manager is None or runtime is None:
            self.state.setText("Model actions are disabled in interface preview mode.")
            for button in (
                self.download_button,
                self.activate_button,
                self.remove_button,
                self.import_button,
            ):
                button.setEnabled(False)
        self.refresh()

    def selected_identifier(self) -> str:
        return str(self.model_combo.currentData())

    def active_identifier(self) -> str:
        return self._runtime.active_model if self._runtime is not None else "small"

    def select_model(self, identifier: str) -> None:
        index = self.model_combo.findData(identifier)
        if index >= 0:
            self.model_combo.setCurrentIndex(index)

    @Slot()
    def refresh(self) -> None:
        identifier = self.selected_identifier()
        spec = next(spec for spec in self._catalogue if spec.identifier == identifier)
        ram = (
            f" Detected RAM: {self._memory_gb:.1f} GB."
            if self._memory_gb is not None
            else ""
        )
        self.details.setText(
            f"{spec.description}\nDownload: {spec.download_size_label}. "
            f"RAM guidance: {spec.minimum_ram_gb} GB or more. "
            f"CPU suitability: {spec.cpu_suitability.value}.{ram}"
        )
        if self._manager is None or self._runtime is None:
            return
        installed = self._manager.is_installed(identifier)
        status = self._manager.status(identifier)
        if status.state in {ModelState.DOWNLOADING, ModelState.VERIFYING}:
            cancellable = (
                status.state is ModelState.DOWNLOADING or status.bytes_total is not None
            )
            self._set_busy(True, cancellable=cancellable)
            self._render_progress(status)
            return
        active = identifier == self.active_identifier()
        if active:
            state = "Installed and active"
        elif installed:
            state = "Installed"
        else:
            state = "Not installed. Download requires an internet connection."
        self.state.setText(state)
        self.download_button.setEnabled(not installed)
        self.activate_button.setEnabled(installed and not active)
        self.remove_button.setEnabled(installed and not active)
        self.import_button.setEnabled(True)

    def _confirm_hardware(self, identifier: str) -> bool:
        spec = next(spec for spec in self._catalogue if spec.identifier == identifier)
        warning = hardware_warning(spec, self._memory_gb)
        if warning is None:
            return True
        answer = QMessageBox.warning(
            self,
            "This model may be slow",
            warning + "\n\nDo you want to continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        return answer == QMessageBox.StandardButton.Yes

    def _set_busy(self, busy: bool, *, cancellable: bool = False) -> None:
        self.model_combo.setEnabled(not busy)
        for button in (
            self.download_button,
            self.activate_button,
            self.remove_button,
            self.import_button,
        ):
            button.setEnabled(not busy)
        self.progress.setVisible(busy)
        self.cancel_button.setVisible(busy and cancellable)
        self.cancel_button.setEnabled(busy and cancellable)
        if busy:
            self.progress.setRange(0, 0)
            self.progress.setFormat("Working locally…")

    def _run(
        self,
        identifier: str,
        operation: Callable[[Callable[[ModelStatus], None]], str],
        *,
        cancellable: bool = False,
    ) -> None:
        self._set_busy(True, cancellable=cancellable)
        signals = _TaskSignals(self)
        self._task_signals = signals
        signals.status.connect(self._status_changed)
        signals.succeeded.connect(self._operation_succeeded)
        signals.failed.connect(self._operation_failed)
        signals.cancelled.connect(self._operation_cancelled)

        def worker() -> None:
            try:
                completed_identifier = operation(signals.status.emit)
            except ModelOperationCancelled as error:
                signals.cancelled.emit(str(error))
            except (
                ModelManagerError,
                ModelActivationError,
                SettingsWriteError,
            ) as error:
                signals.failed.emit(str(error))
            except Exception:
                signals.failed.emit(
                    "The model operation failed safely. The previous model remains "
                    "active."
                )
            else:
                signals.succeeded.emit(completed_identifier)

        threading.Thread(target=worker, daemon=True).start()

    @Slot(object)
    def _status_changed(self, status: ModelStatus) -> None:
        if status.state in {ModelState.DOWNLOADING, ModelState.VERIFYING}:
            self.select_model(status.identifier)
            cancellable = (
                status.state is ModelState.DOWNLOADING or status.bytes_total is not None
            )
            self._set_busy(True, cancellable=cancellable)
            self._render_progress(status)
            return
        if status.state in {
            ModelState.INSTALLED,
            ModelState.NOT_INSTALLED,
            ModelState.ERROR,
        }:
            self._set_busy(False)
            self.select_model(status.identifier)
            self.refresh()
            if status.detail:
                self.state.setText(status.detail)
            return
        self._render_progress(status)

    def _render_progress(self, status: ModelStatus) -> None:
        self.state.setText(status.detail)
        if status.progress is None:
            self.progress.setRange(0, 0)
        else:
            self.progress.setRange(0, 100)
            self.progress.setValue(round(status.progress * 100))
        spec = next(
            spec for spec in self._catalogue if spec.identifier == status.identifier
        )
        stage = "Verifying" if status.state is ModelState.VERIFYING else "Downloading"
        if status.state is ModelState.LOADING:
            self.progress.setFormat(f"Loading {spec.name} locally…")
        elif status.bytes_completed is not None and status.bytes_total:
            completed = status.bytes_completed / 1_000_000
            total = status.bytes_total / 1_000_000
            percent = round((status.bytes_completed / status.bytes_total) * 100)
            self.progress.setFormat(
                f"{stage} {spec.name}: {completed:.0f} MB of {total:.0f} MB "
                f"({percent}%)"
            )
        else:
            self.progress.setFormat(f"{stage} {spec.name}…")

    @Slot(str)
    def _operation_succeeded(self, identifier: str) -> None:
        self._set_busy(False)
        self.select_model(identifier)
        self.refresh()
        if identifier == self.active_identifier():
            self.model_activated.emit(identifier)
        self._task_signals = None

    @Slot(str)
    def _operation_failed(self, message: str) -> None:
        self._set_busy(False)
        self.refresh()
        QMessageBox.critical(self, "Model operation failed", message)
        self._task_signals = None

    @Slot(str)
    def _operation_cancelled(self, message: str) -> None:
        self._set_busy(False)
        self.refresh()
        self.state.setText(message or "Model download cancelled.")
        self._task_signals = None

    @Slot()
    def cancel_active_operation(self) -> None:
        if self._manager is None:
            return
        if self._manager.cancel_active():
            self.cancel_button.setEnabled(False)
            self.state.setText("Cancelling model download…")
            self.progress.setFormat("Cancelling…")

    @Slot()
    def _download(self) -> None:
        if self._manager is None:
            return
        identifier = self.selected_identifier()
        if not self._confirm_hardware(identifier):
            return
        self._run(
            identifier,
            lambda _callback: self._manager.install(identifier).name,
            cancellable=True,
        )

    @Slot()
    def _activate(self) -> None:
        if self._runtime is None:
            return
        identifier = self.selected_identifier()
        if not self._confirm_hardware(identifier):
            return

        def activate(callback) -> str:
            self._runtime.activate(identifier, callback)
            return identifier

        self._run(identifier, activate)

    @Slot()
    def _remove(self) -> None:
        if self._manager is None:
            return
        identifier = self.selected_identifier()
        spec = self._manager.spec(identifier)
        answer = QMessageBox.question(
            self,
            "Remove local speech model",
            f"Remove {spec.name} from this PC? It can be downloaded again later.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return

        def remove(callback) -> str:
            del callback
            self._manager.remove(identifier, active_model=self.active_identifier())
            return identifier

        self._run(identifier, remove)

    @Slot()
    def _import(self) -> None:
        if self._manager is None:
            return
        selected = QFileDialog.getExistingDirectory(
            self,
            "Choose a Bragi model folder",
            str(Path.home()),
        )
        if not selected:
            return

        def import_model(callback) -> str:
            return self._manager.import_directory(Path(selected), callback).name

        self._run(self.selected_identifier(), import_model)
