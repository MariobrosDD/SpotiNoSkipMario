import os
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt, QPoint, QSize
from PyQt6.QtGui import QMouseEvent, QPixmap

_LOGO_PATH = os.path.join(os.path.dirname(__file__), '..', 'assets', 'Spotify Mario.png')


class TitleBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('title_bar')
        self.setFixedHeight(40)
        self._drag_pos: QPoint | None = None
        self._was_maximized = False

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 0, 0)
        layout.setSpacing(8)

        # Logo
        logo_label = QLabel()
        logo_label.setFixedSize(22, 22)
        logo_label.setScaledContents(True)
        px = QPixmap(_LOGO_PATH)
        if not px.isNull():
            logo_label.setPixmap(px)
        layout.addWidget(logo_label)

        name = QLabel('SPOTIFY SKIP PERMISSIONS')
        name.setObjectName('titlebar_name')
        layout.addWidget(name)
        layout.addStretch()

        self._min_btn   = self._btn('−', 'win_btn',       self._minimize)
        self._max_btn   = self._btn('□', 'win_btn',       self._toggle_maximize)
        self._close_btn = self._btn('×', 'win_close_btn', self._close)

        for b in (self._min_btn, self._max_btn, self._close_btn):
            layout.addWidget(b)

    def _btn(self, text, obj_name, slot) -> QPushButton:
        b = QPushButton(text)
        b.setObjectName(obj_name)
        b.setFixedSize(46, 40)
        b.setCursor(Qt.CursorShape.ArrowCursor)
        b.clicked.connect(slot)
        return b

    # ── Acciones ────────────────────────────────────────────

    def _minimize(self):
        self.window().showMinimized()

    def _toggle_maximize(self):
        win = self.window()
        if win.isMaximized():
            win.showNormal()
            self._max_btn.setText('□')
        else:
            win.showMaximized()
            self._max_btn.setText('❐')

    def _close(self):
        self.window().close()

    # ── Arrastrar ventana ────────────────────────────────────

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint()
            self._was_maximized = self.window().isMaximized()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if event.buttons() == Qt.MouseButton.LeftButton and self._drag_pos is not None:
            win = self.window()
            if self._was_maximized:
                win.showNormal()
                self._was_maximized = False
                self._max_btn.setText('□')
                self._drag_pos = event.globalPosition().toPoint()
            win.move(win.pos() + (event.globalPosition().toPoint() - self._drag_pos))
            self._drag_pos = event.globalPosition().toPoint()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        self._drag_pos = None
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self._toggle_maximize()
        super().mouseDoubleClickEvent(event)
