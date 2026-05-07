import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QPushButton, QLineEdit, QApplication)
from PyQt6.QtCore import Qt, QPoint, QTimer, pyqtSignal
from PyQt6.QtGui import QPixmap, QMouseEvent

from src.ui.styles import STYLESHEET

_LOGO_PATH = os.path.join(os.path.dirname(__file__), '..', 'assets', 'Spotify Mario.png')


class RegisterWindow(QWidget):
    registered = pyqtSignal()
    back_to_login = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setFixedSize(420, 580)
        self.setObjectName('auth_window')
        self.setStyleSheet(STYLESHEET)
        self._drag_pos: QPoint | None = None
        self._suppress_signal = False

        screen = QApplication.primaryScreen().availableGeometry()
        self.move(
            (screen.width() - self.width()) // 2,
            (screen.height() - self.height()) // 2,
        )

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Barra de título ──────────────────────────────────
        tbar = QWidget()
        tbar.setFixedHeight(36)
        tbar.setObjectName('auth_titlebar')
        tbar_layout = QHBoxLayout(tbar)
        tbar_layout.setContentsMargins(0, 0, 0, 0)
        tbar_layout.setSpacing(0)
        tbar_layout.addStretch()

        min_btn = QPushButton('−')
        min_btn.setObjectName('win_btn')
        min_btn.setFixedSize(46, 36)
        min_btn.clicked.connect(self.showMinimized)

        close_btn = QPushButton('×')
        close_btn.setObjectName('win_close_btn')
        close_btn.setFixedSize(46, 36)
        close_btn.clicked.connect(self.close)

        tbar_layout.addWidget(min_btn)
        tbar_layout.addWidget(close_btn)
        root.addWidget(tbar)

        # ── Contenido ────────────────────────────────────────
        card = QWidget()
        card.setObjectName('auth_card')
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(48, 16, 48, 32)
        card_layout.setSpacing(0)

        # Logo
        logo_label = QLabel()
        logo_label.setFixedSize(52, 52)
        logo_label.setScaledContents(True)
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        px = QPixmap(_LOGO_PATH)
        if not px.isNull():
            logo_label.setPixmap(px)
        logo_row = QHBoxLayout()
        logo_row.addStretch()
        logo_row.addWidget(logo_label)
        logo_row.addStretch()
        card_layout.addLayout(logo_row)
        card_layout.addSpacing(18)

        title = QLabel('Crear cuenta')
        title.setObjectName('auth_title')
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(title)
        card_layout.addSpacing(6)

        subtitle = QLabel('Regístrate para acceder')
        subtitle.setObjectName('auth_subtitle')
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(subtitle)
        card_layout.addSpacing(30)

        # Campo correo
        email_lbl = QLabel('CORREO ELECTRÓNICO')
        email_lbl.setObjectName('auth_field_label')
        card_layout.addWidget(email_lbl)
        card_layout.addSpacing(6)

        self._email_input = QLineEdit()
        self._email_input.setObjectName('auth_input')
        self._email_input.setPlaceholderText('tu@correo.com')
        self._email_input.setFixedHeight(42)
        card_layout.addWidget(self._email_input)
        card_layout.addSpacing(20)

        # Campo contraseña
        pass_lbl = QLabel('CONTRASEÑA')
        pass_lbl.setObjectName('auth_field_label')
        card_layout.addWidget(pass_lbl)
        card_layout.addSpacing(6)

        pass_row = QHBoxLayout()
        pass_row.setSpacing(0)

        self._pass_input = QLineEdit()
        self._pass_input.setObjectName('auth_input')
        self._pass_input.setPlaceholderText('Mínimo 6 caracteres')
        self._pass_input.setEchoMode(QLineEdit.EchoMode.Password)
        self._pass_input.setFixedHeight(42)

        self._toggle_btn = QPushButton('Mostrar')
        self._toggle_btn.setObjectName('auth_toggle_btn')
        self._toggle_btn.setFixedSize(70, 42)
        self._toggle_btn.setCheckable(True)
        self._toggle_btn.clicked.connect(self._toggle_password)

        pass_row.addWidget(self._pass_input)
        pass_row.addWidget(self._toggle_btn)
        card_layout.addLayout(pass_row)
        card_layout.addSpacing(20)

        # Campo confirmar contraseña
        conf_lbl = QLabel('CONFIRMAR CONTRASEÑA')
        conf_lbl.setObjectName('auth_field_label')
        card_layout.addWidget(conf_lbl)
        card_layout.addSpacing(6)

        self._conf_input = QLineEdit()
        self._conf_input.setObjectName('auth_input')
        self._conf_input.setPlaceholderText('Repite la contraseña')
        self._conf_input.setEchoMode(QLineEdit.EchoMode.Password)
        self._conf_input.setFixedHeight(42)
        self._conf_input.returnPressed.connect(self._on_register)
        card_layout.addWidget(self._conf_input)
        card_layout.addSpacing(18)

        # Mensaje error/éxito
        self._msg_label = QLabel('')
        self._msg_label.setObjectName('auth_error')
        self._msg_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._msg_label.setWordWrap(True)
        self._msg_label.setFixedHeight(18)
        card_layout.addWidget(self._msg_label)
        card_layout.addSpacing(14)

        # Botón registrar
        reg_btn = QPushButton('Crear cuenta')
        reg_btn.setObjectName('auth_primary_btn')
        reg_btn.setFixedHeight(48)
        reg_btn.clicked.connect(self._on_register)
        card_layout.addWidget(reg_btn)
        card_layout.addSpacing(22)

        # Enlace volver
        back_row = QHBoxLayout()
        back_row.addStretch()
        back_lbl = QLabel('¿Ya tienes cuenta?')
        back_lbl.setObjectName('auth_hint')
        back_btn = QPushButton('Iniciar sesión')
        back_btn.setObjectName('auth_link_btn')
        back_btn.clicked.connect(self.back_to_login)
        back_row.addWidget(back_lbl)
        back_row.addSpacing(6)
        back_row.addWidget(back_btn)
        back_row.addStretch()
        card_layout.addLayout(back_row)

        card_layout.addStretch()
        root.addWidget(card)

    # ── Acciones ─────────────────────────────────────────────

    def _toggle_password(self, checked: bool):
        mode = QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password
        self._pass_input.setEchoMode(mode)
        self._toggle_btn.setText('Ocultar' if checked else 'Mostrar')

    def _on_register(self):
        from src.auth.auth_manager import register_user
        email = self._email_input.text().strip()
        password = self._pass_input.text()
        confirm = self._conf_input.text()

        if not email or not password or not confirm:
            self._show_msg('Por favor completa todos los campos.', error=True)
            return
        if password != confirm:
            self._show_msg('Las contraseñas no coinciden.', error=True)
            return

        success, msg = register_user(email, password)
        if success:
            self._show_msg(msg, error=False)
            QTimer.singleShot(1200, self.registered.emit)
        else:
            self._show_msg(msg, error=True)

    def _show_msg(self, msg: str, error: bool = True):
        color = '#FF4444' if error else '#44CC77'
        self._msg_label.setStyleSheet(f'color: {color};')
        self._msg_label.setText(msg)

    def closeEvent(self, event):
        if not self._suppress_signal:
            self.back_to_login.emit()
        super().closeEvent(event)

    # ── Arrastrar ventana ────────────────────────────────────

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if event.buttons() == Qt.MouseButton.LeftButton and self._drag_pos is not None:
            self.move(self.pos() + (event.globalPosition().toPoint() - self._drag_pos))
            self._drag_pos = event.globalPosition().toPoint()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        self._drag_pos = None
        super().mouseReleaseEvent(event)
