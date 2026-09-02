from __future__ import annotations

import threading
from collections.abc import Callable
from pathlib import Path

from PySide6.QtCore import QObject, QSignalBlocker, Qt, Signal, Slot
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from whisper_dictate.i18n import tr
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


def _role(widget: QWidget, name: str) -> QWidget:
    widget.setProperty("uiRole", name)
    return widget


def _label(
    text: str = "", *, parent: QWidget | None = None, role: str | None = None
) -> QLabel:
    label = QLabel(text, parent)
    label.setWordWrap(True)
    if role is not None:
        _role(label, role)
    return label


def _card(parent: QWidget, *, quiet: bool = False) -> tuple[QFrame, QVBoxLayout]:
    frame = QFrame(parent)
    _role(frame, "quietCard" if quiet else "card")
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(18, 16, 18, 17)
    layout.setSpacing(10)
    return frame, layout


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
        self._last_status: ModelStatus | None = None
        self._manager_signals = _TaskSignals(self)
        self._manager_signals.status.connect(self._status_changed)
        if manager is not None:
            manager.add_status_listener(self._manager_signals.status.emit)
        self.setAccessibleName(tr("Local speech models"))

        self.setObjectName("settingsPage")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 16, 6, 14)
        layout.setSpacing(14)

        self.page_title = _label(tr("Speech models"), parent=self, role="pageTitle")
        layout.addWidget(self.page_title)

        self.introduction = _label(
            tr(
                "Choose the balance between speed and accuracy. Models are stored "
                "on this PC and work offline after download."
            ),
            parent=self,
            role="secondary",
        )
        self.introduction.setAccessibleName(
            tr("Model privacy and download explanation")
        )
        layout.addWidget(self.introduction)

        self.model_card, model_layout = _card(self)
        self.model_card_title = _label(
            tr("Choose a model"), parent=self.model_card, role="sectionTitle"
        )
        model_layout.addWidget(self.model_card_title)

        self.model_combo = QComboBox(self)
        self.model_combo.setAccessibleName(tr("Speech model"))
        for spec in self._catalogue:
            label = (
                tr("{name} (recommended)", name=spec.name)
                if spec.recommended
                else spec.name
            )
            self.model_combo.addItem(label, spec.identifier)
        self.model_combo.currentIndexChanged.connect(self.refresh)
        self.model_label = QLabel(f"&{tr('Model')}:", self.model_card)
        self.model_label.setBuddy(self.model_combo)
        model_form = QFormLayout()
        model_form.setFieldGrowthPolicy(
            QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow
        )
        model_form.addRow(self.model_label, self.model_combo)
        model_layout.addLayout(model_form)

        self.details = _label(parent=self.model_card, role="secondary")
        self.details.setAccessibleName(tr("Selected model details"))
        self.details.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByKeyboard
        )
        model_layout.addWidget(self.details)

        self.state = _label(parent=self.model_card, role="statusBadge")
        self.state.setAccessibleName(tr("Selected model status"))
        model_layout.addWidget(self.state)

        self.progress = QProgressBar(self)
        self.progress.setAccessibleName(tr("Model operation progress"))
        self.progress.setTextVisible(True)
        self.progress.hide()
        model_layout.addWidget(self.progress)

        button_row = QHBoxLayout()
        self.download_button = QPushButton(f"&{tr('Download model')}", self)
        self.download_button.setAccessibleName(tr("Download selected model"))
        self.download_button.setProperty("buttonRole", "primary")
        self.activate_button = QPushButton(f"&{tr('Use this model')}", self)
        self.activate_button.setAccessibleName(tr("Use selected speech model"))
        self.activate_button.setProperty("buttonRole", "primary")
        self.remove_button = QPushButton(f"&{tr('Remove from this PC')}", self)
        self.remove_button.setAccessibleName(tr("Remove selected model"))
        self.remove_button.setProperty("buttonRole", "destructive")
        self.import_button = QPushButton(f"&{tr('Choose model folder…')}", self)
        self.import_button.setAccessibleName(tr("Import a Skrivi model folder"))
        self.cancel_button = QPushButton(f"&{tr('Cancel download')}", self)
        self.cancel_button.setAccessibleName(tr("Cancel model download"))
        self.cancel_button.hide()
        button_row.addWidget(self.download_button)
        button_row.addWidget(self.activate_button)
        button_row.addWidget(self.remove_button)
        button_row.addWidget(self.cancel_button)
        button_row.addStretch(1)
        model_layout.addLayout(button_row)
        layout.addWidget(self.model_card)

        self.import_card, import_layout = _card(self, quiet=True)
        self.import_title = _label(
            tr("Already have a model?"), parent=self.import_card, role="sectionTitle"
        )
        import_layout.addWidget(self.import_title)
        self.import_help = _label(
            tr("Import a verified Skrivi model folder copied from another computer."),
            parent=self.import_card,
            role="secondary",
        )
        import_layout.addWidget(self.import_help)
        import_row = QHBoxLayout()
        import_row.addWidget(self.import_button)
        import_row.addStretch(1)
        import_layout.addLayout(import_row)
        layout.addWidget(self.import_card)
        layout.addStretch(1)

        self.download_button.clicked.connect(self._download)
        self.activate_button.clicked.connect(self._activate)
        self.remove_button.clicked.connect(self._remove)
        self.import_button.clicked.connect(self._import)
        self.cancel_button.clicked.connect(self.cancel_active_operation)

        if manager is None or runtime is None:
            self.state.setText(
                tr("Model actions are disabled in interface preview mode.")
            )
            for button in (
                self.download_button,
                self.activate_button,
                self.remove_button,
                self.import_button,
            ):
                button.setEnabled(False)
            for button in (
                self.download_button,
                self.activate_button,
                self.remove_button,
            ):
                button.hide()
        self.refresh()

    def selected_identifier(self) -> str:
        return str(self.model_combo.currentData())

    def active_identifier(self) -> str:
        return self._runtime.active_model if self._runtime is not None else "small"

    def select_model(self, identifier: str) -> None:
        index = self.model_combo.findData(identifier)
        if index >= 0:
            self.model_combo.setCurrentIndex(index)

    def retranslate_ui(self) -> None:
        self.setAccessibleName(tr("Local speech models"))
        self.introduction.setText(
            tr(
                "Choose the balance between speed and accuracy. Models are stored "
                "on this PC and work offline after download."
            )
        )
        self.page_title.setText(tr("Speech models"))
        self.model_card_title.setText(tr("Choose a model"))
        self.model_label.setText(f"&{tr('Model')}:")
        self.introduction.setAccessibleName(
            tr("Model privacy and download explanation")
        )
        selected = self.selected_identifier()
        blocker = QSignalBlocker(self.model_combo)
        self.model_combo.clear()
        for spec in self._catalogue:
            label = (
                tr("{name} (recommended)", name=spec.name)
                if spec.recommended
                else spec.name
            )
            self.model_combo.addItem(label, spec.identifier)
        self.select_model(selected)
        del blocker
        self.model_combo.setAccessibleName(tr("Speech model"))
        self.details.setAccessibleName(tr("Selected model details"))
        self.state.setAccessibleName(tr("Selected model status"))
        self.progress.setAccessibleName(tr("Model operation progress"))
        self.download_button.setText(f"&{tr('Download model')}")
        self.download_button.setAccessibleName(tr("Download selected model"))
        self.activate_button.setText(f"&{tr('Use this model')}")
        self.activate_button.setAccessibleName(tr("Use selected speech model"))
        self.remove_button.setText(f"&{tr('Remove from this PC')}")
        self.remove_button.setAccessibleName(tr("Remove selected model"))
        self.import_title.setText(tr("Already have a model?"))
        self.import_help.setText(
            tr("Import a verified Skrivi model folder copied from another computer.")
        )
        self.import_button.setText(f"&{tr('Choose model folder…')}")
        self.import_button.setAccessibleName(tr("Import a Skrivi model folder"))
        self.cancel_button.setText(f"&{tr('Cancel download')}")
        self.cancel_button.setAccessibleName(tr("Cancel model download"))
        self.refresh()
        if self._manager is None or self._runtime is None:
            self.state.setText(
                tr("Model actions are disabled in interface preview mode.")
            )
        elif self._last_status is not None and self._last_status.state in {
            ModelState.DOWNLOADING,
            ModelState.VERIFYING,
            ModelState.LOADING,
        }:
            self._render_progress(self._last_status)

    @Slot()
    def refresh(self) -> None:
        identifier = self.selected_identifier()
        spec = next(spec for spec in self._catalogue if spec.identifier == identifier)
        ram = (
            tr(" Detected RAM: {memory:.1f} GB.", memory=self._memory_gb)
            if self._memory_gb is not None
            else ""
        )
        self.details.setText(
            tr(spec.description)
            + "\n"
            + tr("Download: {size}.", size=spec.download_size_label)
            + " "
            + tr("RAM guidance: {memory} GB or more.", memory=spec.minimum_ram_gb)
            + " "
            + tr(
                "CPU suitability: {suitability}.{ram}",
                suitability=tr(spec.cpu_suitability.value),
                ram=ram,
            )
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
            state = tr("Installed and active")
        elif installed:
            state = tr("Installed")
        else:
            state = tr("Not installed. Download requires an internet connection.")
        self.state.setText(state)
        self.download_button.setVisible(not installed)
        self.activate_button.setVisible(installed and not active)
        self.remove_button.setVisible(installed and not active)
        self.download_button.setEnabled(not installed)
        self.activate_button.setEnabled(installed and not active)
        self.remove_button.setEnabled(installed and not active)
        self.import_button.setEnabled(True)

    def _confirm_hardware(self, identifier: str) -> bool:
        spec = next(spec for spec in self._catalogue if spec.identifier == identifier)
        warning = hardware_warning(spec, self._memory_gb)
        if warning is None:
            return True
        return self._ask_yes_no(
            tr("This model may be slow"),
            warning + "\n\n" + tr("Do you want to continue?"),
        )

    def _ask_yes_no(self, title: str, text: str) -> bool:
        message = QMessageBox(
            QMessageBox.Icon.Warning,
            title,
            text,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            self,
        )
        yes_button = message.button(QMessageBox.StandardButton.Yes)
        no_button = message.button(QMessageBox.StandardButton.No)
        if yes_button is not None:
            yes_button.setText(tr("Yes"))
        if no_button is not None:
            no_button.setText(tr("No"))
            message.setDefaultButton(no_button)
        return message.exec() == QMessageBox.StandardButton.Yes

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
            for button in (
                self.download_button,
                self.activate_button,
                self.remove_button,
            ):
                button.hide()
            self.progress.setRange(0, 0)
            self.progress.setFormat(tr("Working locally…"))

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
                    tr(
                        "The model operation failed safely. The previous model remains "
                        "active."
                    )
                )
            else:
                signals.succeeded.emit(completed_identifier)

        threading.Thread(target=worker, daemon=True).start()

    @Slot(object)
    def _status_changed(self, status: ModelStatus) -> None:
        self._last_status = status
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
                self.state.setText(tr(status.detail))
            return
        self._render_progress(status)

    def _render_progress(self, status: ModelStatus) -> None:
        spec = next(
            spec for spec in self._catalogue if spec.identifier == status.identifier
        )
        if status.state is ModelState.DOWNLOADING:
            detail = tr("Downloading {name}…", name=spec.name)
        elif status.state is ModelState.VERIFYING:
            detail = tr("Verifying {name}…", name=spec.name)
        elif status.state is ModelState.LOADING:
            detail = tr("Loading {name} locally…", name=spec.name)
        else:
            detail = tr(status.detail)
        self.state.setText(detail)
        if status.progress is None:
            self.progress.setRange(0, 0)
        else:
            self.progress.setRange(0, 100)
            self.progress.setValue(round(status.progress * 100))
        stage = (
            tr("Verifying")
            if status.state is ModelState.VERIFYING
            else tr("Downloading")
        )
        if status.state is ModelState.LOADING:
            self.progress.setFormat(tr("Loading {name} locally…", name=spec.name))
        elif status.bytes_completed is not None and status.bytes_total:
            completed = status.bytes_completed / 1_000_000
            total = status.bytes_total / 1_000_000
            percent = round((status.bytes_completed / status.bytes_total) * 100)
            self.progress.setFormat(
                tr(
                    "{stage} {name}: {completed:.0f} MB of {total:.0f} MB ({percent}%)",
                    stage=stage,
                    name=spec.name,
                    completed=completed,
                    total=total,
                    percent=percent,
                )
            )
        else:
            self.progress.setFormat(tr("{stage} {name}…", stage=stage, name=spec.name))

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
        QMessageBox.critical(self, tr("Model operation failed"), tr(message))
        self._task_signals = None

    @Slot(str)
    def _operation_cancelled(self, message: str) -> None:
        self._set_busy(False)
        self.refresh()
        self.state.setText(tr(message or "Model download cancelled."))
        self._task_signals = None

    @Slot()
    def cancel_active_operation(self) -> None:
        if self._manager is None:
            return
        if self._manager.cancel_active():
            self.cancel_button.setEnabled(False)
            self.state.setText(tr("Cancelling model download…"))
            self.progress.setFormat(tr("Cancelling…"))

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
        if not self._ask_yes_no(
            tr("Remove local speech model"),
            tr(
                "Remove {name} from this PC? It can be downloaded again later.",
                name=spec.name,
            ),
        ):
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
            tr("Choose a Skrivi model folder"),
            str(Path.home()),
        )
        if not selected:
            return

        def import_model(callback) -> str:
            return self._manager.import_directory(Path(selected), callback).name

        self._run(self.selected_identifier(), import_model)
