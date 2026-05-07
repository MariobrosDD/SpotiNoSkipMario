from typing import List, Optional
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QTableWidget, QTableWidgetItem, QHeaderView,
                              QAbstractItemView)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QColor, QPixmap

from src.audio.scanner import Track
from src.utils.image_utils import bytes_to_pixmap, placeholder_pixmap

_COL_NUM    = 0
_COL_COVER  = 1
_COL_TITLE  = 2
_COL_ARTIST = 3
_COL_ALBUM  = 4
_COL_DURATION = 5
_COL_FORMAT = 6

_HEADERS = ['#', '', 'TÍTULO', 'ARTISTA', 'ÁLBUM', 'DURACIÓN', 'FORMATO']
_ROW_HEIGHT  = 52
_COVER_SIZE  = 40

_COLOR_PLAYING_BG = QColor('#1A1A1A')
_COLOR_DIM    = QColor('#FFFFFF')
_COLOR_NORMAL = QColor('#FFFFFF')
_COLOR_WHITE  = QColor('#FFFFFF')
_COLOR_CLEAR  = QColor(0, 0, 0, 0)

_placeholder = None


def _get_placeholder() -> QPixmap:
    global _placeholder
    if _placeholder is None:
        _placeholder = placeholder_pixmap(_COVER_SIZE)
    return _placeholder


def _cover_label(cover_data: Optional[bytes], grayscale: bool = False) -> QLabel:
    label = QLabel()
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    label.setStyleSheet('background: transparent;')

    if cover_data:
        px = bytes_to_pixmap(cover_data, grayscale=grayscale)
    else:
        px = None

    pixmap = px if px else _get_placeholder()
    scaled = pixmap.scaled(_COVER_SIZE, _COVER_SIZE,
                           Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                           Qt.TransformationMode.SmoothTransformation)
    label.setPixmap(scaled)
    return label


class TrackList(QWidget):
    track_activated = pyqtSignal(object, int)  # Track, index

    def __init__(self, parent=None):
        super().__init__(parent)
        self._tracks: List[Track] = []
        self._playing_row: int = -1

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Cabecera
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(24, 20, 24, 8)

        self._title_label = QLabel('Todas las canciones')
        self._title_label.setStyleSheet('font-size: 22px; font-weight: bold; color: #FFFFFF;')
        self._count_label = QLabel('')
        self._count_label.setStyleSheet('font-size: 12px; color: #FFFFFF;')

        header_layout.addWidget(self._title_label)
        header_layout.addStretch()
        header_layout.addWidget(self._count_label)
        layout.addWidget(header_widget)

        # Estado vacío
        self._empty_label = QLabel('No hay canciones.\nUsa la barra lateral para añadir una carpeta.')
        self._empty_label.setObjectName('empty_label')
        self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._empty_label)

        # Tabla
        self._table = QTableWidget()
        self._table.setColumnCount(len(_HEADERS))
        self._table.setHorizontalHeaderLabels(_HEADERS)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setShowGrid(False)
        self._table.verticalHeader().setVisible(False)
        self._table.horizontalHeader().setHighlightSections(False)
        self._table.setAlternatingRowColors(False)
        self._table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._table.setVisible(False)

        vh = self._table.verticalHeader()
        vh.setDefaultSectionSize(_ROW_HEIGHT)
        vh.setSectionResizeMode(QHeaderView.ResizeMode.Fixed)

        hh = self._table.horizontalHeader()
        hh.setSectionResizeMode(_COL_NUM,      QHeaderView.ResizeMode.Fixed)
        hh.setSectionResizeMode(_COL_COVER,    QHeaderView.ResizeMode.Fixed)
        hh.setSectionResizeMode(_COL_TITLE,    QHeaderView.ResizeMode.Stretch)
        hh.setSectionResizeMode(_COL_ARTIST,   QHeaderView.ResizeMode.Fixed)
        hh.setSectionResizeMode(_COL_ALBUM,    QHeaderView.ResizeMode.Fixed)
        hh.setSectionResizeMode(_COL_DURATION, QHeaderView.ResizeMode.Fixed)
        hh.setSectionResizeMode(_COL_FORMAT,   QHeaderView.ResizeMode.Fixed)

        self._table.setColumnWidth(_COL_NUM,      44)
        self._table.setColumnWidth(_COL_COVER,    _COVER_SIZE + 12)
        self._table.setColumnWidth(_COL_ARTIST,   180)
        self._table.setColumnWidth(_COL_ALBUM,    180)
        self._table.setColumnWidth(_COL_DURATION, 70)
        self._table.setColumnWidth(_COL_FORMAT,   60)

        self._table.doubleClicked.connect(self._on_double_click)
        layout.addWidget(self._table)

    def set_header(self, text: str):
        self._title_label.setText(text)

    def set_tracks(self, tracks: List[Track]):
        self._tracks = tracks
        self._playing_row = -1
        self._table.setRowCount(0)

        if not tracks:
            self._table.setVisible(False)
            self._empty_label.setVisible(True)
            self._count_label.setText('')
            return

        self._empty_label.setVisible(False)
        self._table.setVisible(True)
        self._table.setRowCount(len(tracks))

        for i, track in enumerate(tracks):
            self._set_row(i, track)

        n = len(tracks)
        self._count_label.setText(f'{n} canción{"es" if n != 1 else ""}')

    def _set_row(self, row: int, track: Track):
        num_item = QTableWidgetItem(str(row + 1))
        num_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
        num_item.setForeground(_COLOR_DIM)

        title_item = QTableWidgetItem(track.title or '—')
        title_item.setForeground(_COLOR_WHITE)

        artist_item = QTableWidgetItem(track.artist or '—')
        artist_item.setForeground(_COLOR_NORMAL)

        album_item = QTableWidgetItem(track.album or '—')
        album_item.setForeground(_COLOR_NORMAL)

        dur_item = QTableWidgetItem(track.duration_str)
        dur_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        dur_item.setForeground(_COLOR_DIM)

        fmt_item = QTableWidgetItem(track.fmt)
        fmt_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
        fmt_item.setForeground(_COLOR_DIM)

        self._table.setItem(row, _COL_NUM,      num_item)
        self._table.setItem(row, _COL_TITLE,    title_item)
        self._table.setItem(row, _COL_ARTIST,   artist_item)
        self._table.setItem(row, _COL_ALBUM,    album_item)
        self._table.setItem(row, _COL_DURATION, dur_item)
        self._table.setItem(row, _COL_FORMAT,   fmt_item)

        # Carátula como widget
        self._table.setCellWidget(row, _COL_COVER, _cover_label(track.cover_data, grayscale=False))

    def set_playing_row(self, row: int):
        if 0 <= self._playing_row < self._table.rowCount():
            self._restore_row(self._playing_row)

        self._playing_row = row

        if 0 <= row < self._table.rowCount():
            for col in range(self._table.columnCount()):
                item = self._table.item(row, col)
                if item:
                    item.setBackground(_COLOR_PLAYING_BG)

            num_item = self._table.item(row, _COL_NUM)
            if num_item:
                num_item.setText('▶')
                num_item.setForeground(_COLOR_WHITE)

            # Fondo también en la celda de carátula (es widget, no item)
            cover_w = self._table.cellWidget(row, _COL_COVER)
            if cover_w:
                cover_w.setStyleSheet('background: #1A1A1A;')

    def _restore_row(self, row: int):
        for col in range(self._table.columnCount()):
            item = self._table.item(row, col)
            if item:
                item.setBackground(_COLOR_CLEAR)

        num_item = self._table.item(row, _COL_NUM)
        if num_item:
            num_item.setText(str(row + 1))
            num_item.setForeground(_COLOR_DIM)

        cover_w = self._table.cellWidget(row, _COL_COVER)
        if cover_w:
            cover_w.setStyleSheet('background: transparent;')

    def find_track_row(self, track: Track) -> int:
        for i, t in enumerate(self._tracks):
            if t.path == track.path:
                return i
        return -1

    def track_count(self) -> int:
        return len(self._tracks)

    def get_track(self, index: int) -> Optional[Track]:
        if 0 <= index < len(self._tracks):
            return self._tracks[index]
        return None

    def _on_double_click(self, index):
        row = index.row()
        if 0 <= row < len(self._tracks):
            self.track_activated.emit(self._tracks[row], row)
