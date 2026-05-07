import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QPushButton, QButtonGroup, QFrame, QSlider)
from PyQt6.QtCore import pyqtSignal, Qt


class Sidebar(QWidget):
    all_songs_requested  = pyqtSignal()
    folder_selected      = pyqtSignal(str)
    add_folder_requested = pyqtSignal()
    logout_requested     = pyqtSignal()
    effects_changed      = pyqtSignal(bool, float, float, float)  # enabled, room, mix, width

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('sidebar')
        self.setFixedWidth(220)

        self._folder_buttons: dict[str, QPushButton] = {}
        self._nav_group = QButtonGroup(self)
        self._nav_group.setExclusive(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 18, 12, 12)
        layout.setSpacing(0)

        # ── Biblioteca ───────────────────────────────────────
        lib_label = QLabel('BIBLIOTECA')
        lib_label.setObjectName('section_label')
        layout.addWidget(lib_label)
        layout.addSpacing(6)

        self._all_btn = QPushButton('Todas las canciones')
        self._all_btn.setObjectName('nav_btn')
        self._all_btn.setCheckable(True)
        self._all_btn.setChecked(True)
        self._all_btn.clicked.connect(self.all_songs_requested)
        self._nav_group.addButton(self._all_btn)
        layout.addWidget(self._all_btn)
        layout.addSpacing(20)

        # ── Carpetas ─────────────────────────────────────────
        folders_label = QLabel('CARPETAS')
        folders_label.setObjectName('section_label')
        layout.addWidget(folders_label)
        layout.addSpacing(6)

        self._folders_layout = QVBoxLayout()
        self._folders_layout.setSpacing(2)
        layout.addLayout(self._folders_layout)
        layout.addSpacing(6)

        self._add_btn = QPushButton('+ Añadir carpeta')
        self._add_btn.setObjectName('add_folder_btn')
        self._add_btn.clicked.connect(self.add_folder_requested)
        layout.addWidget(self._add_btn)
        layout.addSpacing(20)

        # ── Efectos espaciales ───────────────────────────────
        fx_header = QHBoxLayout()
        fx_lbl = QLabel('EFECTOS ESPACIALES')
        fx_lbl.setObjectName('section_label')
        fx_header.addWidget(fx_lbl)
        fx_header.addStretch()
        self._fx_toggle = QPushButton('OFF')
        self._fx_toggle.setObjectName('fx_toggle_btn')
        self._fx_toggle.setCheckable(True)
        self._fx_toggle.setFixedSize(38, 20)
        self._fx_toggle.clicked.connect(self._on_toggle)
        fx_header.addWidget(self._fx_toggle)
        layout.addLayout(fx_header)
        layout.addSpacing(10)

        self._fx_container = QWidget()
        self._fx_container.setEnabled(False)
        fx_layout = QVBoxLayout(self._fx_container)
        fx_layout.setContentsMargins(0, 0, 0, 0)
        fx_layout.setSpacing(8)

        self._room_slider, self._room_val = self._make_slider(fx_layout, 'SALA', 30)
        self._mix_slider,  self._mix_val  = self._make_slider(fx_layout, 'MEZCLA', 25)
        self._width_slider, self._width_val = self._make_slider(fx_layout, 'AMPLITUD', 50)

        layout.addWidget(self._fx_container)
        layout.addStretch()

        # ── Usuario + logout ──────────────────────────────────
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet('color: #1C1C1C;')
        layout.addWidget(sep)
        layout.addSpacing(10)

        self._user_label = QLabel('')
        self._user_label.setObjectName('sidebar_user_label')
        self._user_label.setWordWrap(True)
        layout.addWidget(self._user_label)
        layout.addSpacing(6)

        logout_btn = QPushButton('Cerrar sesión')
        logout_btn.setObjectName('logout_btn')
        logout_btn.clicked.connect(self.logout_requested)
        layout.addWidget(logout_btn)

    # ── Helpers ───────────────────────────────────────────────

    def _make_slider(self, layout: QVBoxLayout, label: str, default: int):
        row = QHBoxLayout()
        lbl = QLabel(label)
        lbl.setObjectName('fx_param_label')
        val = QLabel(str(default))
        val.setObjectName('fx_value_label')
        val.setFixedWidth(26)
        row.addWidget(lbl)
        row.addStretch()
        row.addWidget(val)
        layout.addLayout(row)

        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setObjectName('fx_slider')
        slider.setRange(0, 100)
        slider.setValue(default)
        slider.valueChanged.connect(lambda v, w=val: w.setText(str(v)))
        slider.valueChanged.connect(self._emit_effects)
        layout.addWidget(slider)
        return slider, val

    def _on_toggle(self, checked: bool):
        self._fx_toggle.setText('ON' if checked else 'OFF')
        self._fx_container.setEnabled(checked)
        self._emit_effects()

    def _emit_effects(self):
        enabled = self._fx_toggle.isChecked()
        room  = self._room_slider.value()  / 100.0
        mix   = self._mix_slider.value()   / 100.0
        width = self._width_slider.value() / 50.0   # 0-2x
        self.effects_changed.emit(enabled, room, mix, width)

    def set_user(self, email: str):
        self._user_label.setText(email)

    # ── Carpetas ──────────────────────────────────────────────

    def add_folder(self, folder_path: str):
        if folder_path in self._folder_buttons:
            return
        name = os.path.basename(folder_path) or folder_path
        btn = QPushButton(name)
        btn.setObjectName('folder_btn')
        btn.setCheckable(True)
        btn.setToolTip(folder_path)
        btn.clicked.connect(lambda checked, p=folder_path: self.folder_selected.emit(p))
        self._nav_group.addButton(btn)
        self._folder_buttons[folder_path] = btn
        self._folders_layout.addWidget(btn)

    def remove_folder(self, folder_path: str):
        btn = self._folder_buttons.pop(folder_path, None)
        if btn:
            self._nav_group.removeButton(btn)
            btn.deleteLater()

    def select_all_songs(self):
        self._all_btn.setChecked(True)
