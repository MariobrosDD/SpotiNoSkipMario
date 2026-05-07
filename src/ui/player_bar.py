from typing import Optional
from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QLabel,
                              QPushButton, QSlider, QSizePolicy)
from PyQt6.QtCore import pyqtSignal, Qt, QSize
from PyQt6.QtGui import QPixmap

from src.audio.scanner import Track
from src.utils.image_utils import bytes_to_pixmap, placeholder_pixmap
from src.utils.icons import play_icon, pause_icon, prev_icon, next_icon, shuffle_icon, repeat_icon, repeat_one_icon

_ICON_CTRL = 20
_ICON_PLAY = 18
_ICON_SEC = 18


def _ms_to_str(ms: int) -> str:
    s = ms // 1000
    return f'{s // 60}:{s % 60:02d}'


class _SeekSlider(QSlider):
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.maximum() > 0:
            ratio = event.position().x() / max(self.width(), 1)
            self.setValue(int(ratio * self.maximum()))
        super().mousePressEvent(event)


class PlayerBar(QWidget):
    play_pause_clicked = pyqtSignal()
    prev_clicked = pyqtSignal()
    next_clicked = pyqtSignal()
    seek_requested = pyqtSignal(int)
    volume_changed = pyqtSignal(int)
    shuffle_toggled = pyqtSignal(bool)
    repeat_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('player_bar')
        self.setFixedHeight(90)

        self._current_cover: Optional[bytes] = None
        self._duration_ms = 0
        self._user_seeking = False

        root = QHBoxLayout(self)
        root.setContentsMargins(20, 0, 20, 0)
        root.setSpacing(0)

        # ── Izquierda: carátula + info ─────────────────────
        left = QHBoxLayout()
        left.setSpacing(12)
        left.setContentsMargins(0, 0, 0, 0)

        self._cover_label = QLabel()
        self._cover_label.setFixedSize(56, 56)
        self._cover_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._cover_label.setStyleSheet('background-color: #1A1A1A; border-radius: 3px;')
        self._set_cover_pixmap(placeholder_pixmap(56))
        left.addWidget(self._cover_label)

        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self._title_label = QLabel('—')
        self._title_label.setObjectName('track_title')
        self._title_label.setMaximumWidth(220)

        self._meta_label = QLabel('')
        self._meta_label.setObjectName('track_meta')
        self._meta_label.setMaximumWidth(220)

        info_layout.addWidget(self._title_label)
        info_layout.addWidget(self._meta_label)
        left.addLayout(info_layout)

        left_widget = QWidget()
        left_widget.setLayout(left)
        left_widget.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)

        # ── Centro: controles + progreso ───────────────────
        center = QVBoxLayout()
        center.setSpacing(6)
        center.setContentsMargins(20, 10, 20, 10)
        center.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        btns = QHBoxLayout()
        btns.setSpacing(8)
        btns.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        self._shuffle_btn = QPushButton()
        self._shuffle_btn.setObjectName('secondary_btn')
        self._shuffle_btn.setIcon(shuffle_icon(_ICON_SEC, '#666666'))
        self._shuffle_btn.setIconSize(QSize(_ICON_SEC, _ICON_SEC))
        self._shuffle_btn.setToolTip('Aleatorio')
        self._shuffle_btn.setCheckable(True)
        self._shuffle_btn.toggled.connect(self._on_shuffle_toggled)

        self._prev_btn = QPushButton()
        self._prev_btn.setObjectName('ctrl_btn')
        self._prev_btn.setIcon(prev_icon(_ICON_CTRL, '#FFFFFF'))
        self._prev_btn.setIconSize(QSize(_ICON_CTRL, _ICON_CTRL))
        self._prev_btn.setToolTip('Anterior')
        self._prev_btn.clicked.connect(self.prev_clicked)

        self._play_btn = QPushButton()
        self._play_btn.setObjectName('play_btn')
        self._play_btn.setIcon(play_icon(_ICON_PLAY, '#000000'))
        self._play_btn.setIconSize(QSize(_ICON_PLAY, _ICON_PLAY))
        self._play_btn.setToolTip('Reproducir / Pausar')
        self._play_btn.clicked.connect(self.play_pause_clicked)

        self._next_btn = QPushButton()
        self._next_btn.setObjectName('ctrl_btn')
        self._next_btn.setIcon(next_icon(_ICON_CTRL, '#FFFFFF'))
        self._next_btn.setIconSize(QSize(_ICON_CTRL, _ICON_CTRL))
        self._next_btn.setToolTip('Siguiente')
        self._next_btn.clicked.connect(self.next_clicked)

        self._repeat_btn = QPushButton()
        self._repeat_btn.setObjectName('secondary_btn')
        self._repeat_btn.setIcon(repeat_icon(_ICON_SEC, '#666666'))
        self._repeat_btn.setIconSize(QSize(_ICON_SEC, _ICON_SEC))
        self._repeat_btn.setToolTip('Repetir')
        self._repeat_btn.setCheckable(True)
        self._repeat_btn.clicked.connect(self.repeat_clicked)

        btns.addWidget(self._shuffle_btn)
        btns.addWidget(self._prev_btn)
        btns.addWidget(self._play_btn)
        btns.addWidget(self._next_btn)
        btns.addWidget(self._repeat_btn)
        center.addLayout(btns)

        progress = QHBoxLayout()
        progress.setSpacing(8)

        self._elapsed_label = QLabel('0:00')
        self._elapsed_label.setObjectName('time_label')
        self._elapsed_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self._seek_slider = _SeekSlider(Qt.Orientation.Horizontal)
        self._seek_slider.setObjectName('seek_slider')
        self._seek_slider.setRange(0, 0)
        self._seek_slider.sliderPressed.connect(self._on_seek_pressed)
        self._seek_slider.sliderReleased.connect(self._on_seek_released)

        self._total_label = QLabel('0:00')
        self._total_label.setObjectName('time_label')
        self._total_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        progress.addWidget(self._elapsed_label)
        progress.addWidget(self._seek_slider)
        progress.addWidget(self._total_label)
        center.addLayout(progress)

        center_widget = QWidget()
        center_widget.setLayout(center)
        center_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # ── Derecha: volumen ────────────────────────────────
        right = QHBoxLayout()
        right.setSpacing(10)
        right.setContentsMargins(0, 0, 0, 0)
        right.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        vol_icon = QLabel('♪')
        vol_icon.setStyleSheet('color: #FFFFFF; font-size: 14px;')

        self._vol_slider = QSlider(Qt.Orientation.Horizontal)
        self._vol_slider.setObjectName('vol_slider')
        self._vol_slider.setRange(0, 100)
        self._vol_slider.setValue(80)
        self._vol_slider.setFixedWidth(90)
        self._vol_slider.valueChanged.connect(self.volume_changed)

        right.addWidget(vol_icon)
        right.addWidget(self._vol_slider)

        right_widget = QWidget()
        right_widget.setLayout(right)
        right_widget.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)

        root.addWidget(left_widget, 2)
        root.addWidget(center_widget, 3)
        root.addWidget(right_widget, 2)

    # ── API pública ─────────────────────────────────────────

    def set_track(self, track: Track):
        self._title_label.setText(track.title or '—')
        meta_parts = [p for p in [track.artist, track.album] if p]
        self._meta_label.setText('  ·  '.join(meta_parts) if meta_parts else '')
        self._current_cover = track.cover_data
        self._update_cover()

    def set_playing(self, playing: bool):
        icon = pause_icon(_ICON_PLAY, '#000000') if playing else play_icon(_ICON_PLAY, '#000000')
        self._play_btn.setIcon(icon)

    def set_position(self, ms: int):
        if self._user_seeking:
            return
        self._seek_slider.blockSignals(True)
        self._seek_slider.setValue(ms)
        self._seek_slider.blockSignals(False)
        self._elapsed_label.setText(_ms_to_str(ms))

    def set_duration(self, ms: int):
        self._duration_ms = ms
        self._seek_slider.setRange(0, max(ms, 0))
        self._total_label.setText(_ms_to_str(ms))

    def clear(self):
        self._title_label.setText('—')
        self._meta_label.setText('')
        self._current_cover = None
        self._set_cover_pixmap(placeholder_pixmap(56))
        self._seek_slider.setValue(0)
        self._seek_slider.setRange(0, 0)
        self._elapsed_label.setText('0:00')
        self._total_label.setText('0:00')
        self._play_btn.setIcon(play_icon(_ICON_PLAY, '#000000'))

    # ── Interno ─────────────────────────────────────────────

    def _update_cover(self):
        if self._current_cover:
            px = bytes_to_pixmap(self._current_cover, grayscale=False)
            if px:
                self._set_cover_pixmap(px)
                return
        self._set_cover_pixmap(placeholder_pixmap(56))

    def _set_cover_pixmap(self, pixmap: QPixmap):
        scaled = pixmap.scaled(56, 56, Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                               Qt.TransformationMode.SmoothTransformation)
        self._cover_label.setPixmap(scaled)

    def set_repeat_mode(self, mode: int):
        """Cambia el icono y estado del botón repeat según el modo (0=off, 1=all, 2=one)."""
        if mode == 0:
            self._repeat_btn.setIcon(repeat_icon(_ICON_SEC, '#666666'))
            self._repeat_btn.setChecked(False)
        elif mode == 1:
            self._repeat_btn.setIcon(repeat_icon(_ICON_SEC, '#FFFFFF'))
            self._repeat_btn.setChecked(True)
        else:  # mode == 2
            self._repeat_btn.setIcon(repeat_one_icon(_ICON_SEC, '#FFFFFF'))
            self._repeat_btn.setChecked(True)

    def _on_shuffle_toggled(self, checked: bool):
        color = '#FFFFFF' if checked else '#666666'
        self._shuffle_btn.setIcon(shuffle_icon(_ICON_SEC, color))
        self.shuffle_toggled.emit(checked)

    def _on_seek_pressed(self):
        self._user_seeking = True

    def _on_seek_released(self):
        self._user_seeking = False
        self.seek_requested.emit(self._seek_slider.value())
