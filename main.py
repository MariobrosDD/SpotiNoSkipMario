import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon


def main():
    app = QApplication(sys.argv)
    app.setApplicationName('Spotify Skip Permissions')
    app.setStyle('Fusion')

    logo = os.path.join(os.path.dirname(__file__), 'src', 'assets', 'Spotify Mario.png')
    if os.path.isfile(logo):
        app.setWindowIcon(QIcon(logo))

    from src.auth.auth_manager import load_session, save_session, clear_session

    _ref = []  # mantiene referencias vivas

    def show_main(email: str):
        save_session(email)
        from src.ui.main_window import MainWindow
        main_win = MainWindow(email)
        _ref.append(main_win)
        main_win.show()

        def on_logout():
            clear_session()
            _ref.remove(main_win)
            main_win.close()
            show_login()

        main_win.logout_requested.connect(on_logout)

    def show_login():
        from src.ui.login_window import LoginWindow
        login_win = LoginWindow()
        _ref.append(login_win)
        login_win.show()

        def on_login(email: str):
            _ref.remove(login_win)
            login_win.close()
            show_main(email)

        login_win.login_successful.connect(on_login)

    # Comprobar sesión guardada
    saved_email = load_session()
    if saved_email:
        show_main(saved_email)
    else:
        show_login()

    sys.exit(app.exec())


if __name__ == '__main__':
    main()
