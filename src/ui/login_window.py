import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QPushButton, QLineEdit, QApplication)
from PyQt6.QtCore import Qt, QPoint, pyqtSignal
from PyQt6.QtGui import QPixmap, QMouseEvent

from src.ui.styles import STYLESHEET

_LOGO_PATH = os.path.join(os.path.dirname(__file__), '..', 'assets', 'Spotify Mario.png')


class LoginWindow(QWidget):
    login_successful = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setFixedSize(420, 520)
        self.setObjectName('auth_window')
        self.setStyleSheet(STYLESHEET)
        self._drag_pos: QPoint | None = None

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
        card_layout.setContentsMargins(48, 20, 48, 40)
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
        card_layout.addSpacing(22)

        title = QLabel('Iniciar sesión')
        title.setObjectName('auth_title')
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(title)
        card_layout.addSpacing(6)

        subtitle = QLabel('Bienvenido de nuevo')
        subtitle.setObjectName('auth_subtitle')
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(subtitle)
        card_layout.addSpacing(36)

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
        card_layout.addSpacing(22)

        # Campo contraseña
        pass_lbl = QLabel('CONTRASEÑA')
        pass_lbl.setObjectName('auth_field_label')
        card_layout.addWidget(pass_lbl)
        card_layout.addSpacing(6)

        pass_row = QHBoxLayout()
        pass_row.setSpacing(0)

        self._pass_input = QLineEdit()
        self._pass_input.setObjectName('auth_input')
        self._pass_input.setPlaceholderText('••••••••')
        self._pass_input.setEchoMode(QLineEdit.EchoMode.Password)
        self._pass_input.setFixedHeight(42)
        self._pass_input.returnPressed.connect(self._on_login)

        self._toggle_btn = QPushButton('Mostrar')
        self._toggle_btn.setObjectName('auth_toggle_btn')
        self._toggle_btn.setFixedSize(70, 42)
        self._toggle_btn.setCheckable(True)
        self._toggle_btn.clicked.connect(self._toggle_password)

        pass_row.addWidget(self._pass_input)
        pass_row.addWidget(self._toggle_btn)
        card_layout.addLayout(pass_row)
        card_layout.addSpacing(18)

        # Error
        self._error_label = QLabel('')
        self._error_label.setObjectName('auth_error')
        self._error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._error_label.setWordWrap(True)
        self._error_label.setFixedHeight(18)
        card_layout.addWidget(self._error_label)
        card_layout.addSpacing(14)

        # Botón login
        login_btn = QPushButton('Iniciar sesión')
        login_btn.setObjectName('auth_primary_btn')
        login_btn.setFixedHeight(48)
        login_btn.clicked.connect(self._on_login)
        card_layout.addWidget(login_btn)
        card_layout.addSpacing(24)

        # Enlace registro
        reg_row = QHBoxLayout()
        reg_row.addStretch()
        reg_lbl = QLabel('¿No tienes cuenta?')
        reg_lbl.setObjectName('auth_hint')
        reg_btn = QPushButton('Registrarse')
        reg_btn.setObjectName('auth_link_btn')
        reg_btn.clicked.connect(self._open_register)
        reg_row.addWidget(reg_lbl)
        reg_row.addSpacing(6)
        reg_row.addWidget(reg_btn)
        reg_row.addStretch()
        card_layout.addLayout(reg_row)

        card_layout.addStretch()
        root.addWidget(card)

    # ── Acciones ─────────────────────────────────────────────

    def _toggle_password(self, checked: bool):
        mode = QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password
        self._pass_input.setEchoMode(mode)
        self._toggle_btn.setText('Ocultar' if checked else 'Mostrar')

    def _on_login(self):
        from src.auth.auth_manager import login_user
        email = self._email_input.text().strip()
        password = self._pass_input.text()

        if not email or not password:
            self._error_label.setText('Por favor completa todos los campos.')
            return

        success, result = login_user(email, password)
        if success:
            self._error_label.setText('')
            self.login_successful.emit(result)
        else:
            self._error_label.setText(result)

    def _open_register(self):
        from src.ui.register_window import RegisterWindow
        self._register_win = RegisterWindow()
        self._register_win.registered.connect(self._on_registered)
        self._register_win.back_to_login.connect(self._on_back_to_login)
        self.hide()
        self._register_win.show()

    def _on_registered(self):
        self._register_win._suppress_signal = True
        self._register_win.close()
        self._email_input.clear()
        self._pass_input.clear()
        self._error_label.setText('')
        self.show()

    def _on_back_to_login(self):
        if hasattr(self, '_register_win') and self._register_win.isVisible():
            self._register_win._suppress_signal = True
            self._register_win.close()
        self.show()

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
