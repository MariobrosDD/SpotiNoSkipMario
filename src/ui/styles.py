STYLESHEET = """
* {
    font-family: "Bahnschrift", "Segoe UI", sans-serif;
    font-size: 13px;
    font-weight: 600;
    outline: none;
}

QMainWindow, QWidget {
    background-color: #000000;
    color: #FFFFFF;
    border: none;
}

/* ── Title bar ──────────────────────────────────── */
#title_bar {
    background-color: #000000;
    border-bottom: 1px solid #1C1C1C;
}

#titlebar_name {
    font-size: 11px;
    font-weight: bold;
    color: #FFFFFF;
    letter-spacing: 2px;
}

QPushButton#win_btn {
    background-color: transparent;
    color: #FFFFFF;
    border: none;
    font-size: 17px;
    border-radius: 0;
}
QPushButton#win_btn:hover { background-color: #1C1C1C; }

QPushButton#win_close_btn {
    background-color: transparent;
    color: #FFFFFF;
    border: none;
    font-size: 18px;
    border-radius: 0;
}
QPushButton#win_close_btn:hover { background-color: #FFFFFF; color: #000000; }

/* ── Sidebar ────────────────────────────────────── */
#sidebar {
    background-color: #0A0A0A;
    border-right: 1px solid #1C1C1C;
}

#app_title {
    font-size: 18px;
    font-weight: bold;
    color: #FFFFFF;
    letter-spacing: 1px;
}

#section_label {
    color: #FFFFFF;
    font-size: 10px;
    font-weight: bold;
    letter-spacing: 1.5px;
}

QPushButton#nav_btn {
    background-color: transparent;
    color: #FFFFFF;
    text-align: left;
    padding: 7px 10px;
    border: none;
    border-radius: 5px;
    font-size: 13px;
}
QPushButton#nav_btn:hover   { background-color: #1A1A1A; color: #FFFFFF; }
QPushButton#nav_btn:checked { background-color: #FFFFFF; color: #000000; font-weight: bold; }

QPushButton#folder_btn {
    background-color: transparent;
    color: #FFFFFF;
    text-align: left;
    padding: 6px 10px;
    border: none;
    border-radius: 5px;
    font-family: "Bahnschrift";
    font-size: 14px;
    font-weight: bold;
}
QPushButton#folder_btn:hover   { background-color: #1A1A1A; color: #FFFFFF; }
QPushButton#folder_btn:checked { background-color: #1F1F1F; color: #FFFFFF; }

QPushButton#add_folder_btn {
    background-color: transparent;
    color: #FFFFFF;
    text-align: left;
    padding: 6px 10px;
    border: 1px dashed #444444;
    border-radius: 5px;
    font-size: 12px;
}
QPushButton#add_folder_btn:hover { color: #FFFFFF; border-color: #888888; }

/* ── Track list ─────────────────────────────────── */
QTableWidget {
    background-color: #000000;
    border: none;
    gridline-color: transparent;
    selection-background-color: transparent;
}

QTableWidget::item {
    color: #FFFFFF;
    padding: 0 8px;
    border-bottom: 1px solid #0D0D0D;
}
QTableWidget::item:hover    { background-color: #141414; color: #FFFFFF; }
QTableWidget::item:selected { background-color: #1C1C1C; color: #FFFFFF; }

QHeaderView::section {
    background-color: #000000;
    color: #FFFFFF;
    padding: 6px 8px;
    border: none;
    border-bottom: 1px solid #1C1C1C;
    font-size: 10px;
    font-weight: bold;
    letter-spacing: 0.8px;
    text-transform: uppercase;
}

QScrollBar:vertical {
    background: transparent;
    width: 5px;
}
QScrollBar::handle:vertical {
    background: #2A2A2A;
    border-radius: 3px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover { background: #555555; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: transparent; }

/* ── Player bar ─────────────────────────────────── */
#player_bar {
    background-color: #111111;
    border-top: 1px solid #222222;
}

#track_title { color: #FFFFFF; font-size: 13px; font-weight: bold; }
#track_meta  { color: #FFFFFF; font-size: 11px; }
#time_label  { color: #FFFFFF; font-size: 11px; font-family: "Consolas"; min-width: 38px; }

/* Progress slider */
QSlider#seek_slider::groove:horizontal {
    height: 3px;
    background: #2A2A2A;
    border-radius: 2px;
}
QSlider#seek_slider::sub-page:horizontal {
    background: #FFFFFF;
    border-radius: 2px;
}
QSlider#seek_slider::handle:horizontal {
    background: #FFFFFF;
    width: 14px; height: 14px;
    margin: -6px 0;
    border-radius: 7px;
}
QSlider#seek_slider::handle:horizontal:hover {
    width: 16px; height: 16px;
    margin: -7px 0;
    border-radius: 8px;
}

/* Volume slider */
QSlider#vol_slider::groove:horizontal {
    height: 3px;
    background: #2A2A2A;
    border-radius: 2px;
}
QSlider#vol_slider::sub-page:horizontal {
    background: #FFFFFF;
    border-radius: 2px;
}
QSlider#vol_slider::handle:horizontal {
    background: #FFFFFF;
    width: 12px; height: 12px;
    margin: -5px 0;
    border-radius: 6px;
}

/* Control buttons */
QPushButton#ctrl_btn {
    background-color: transparent;
    color: #FFFFFF;
    border: none;
    font-size: 16px;
    padding: 4px 6px;
    border-radius: 4px;
    min-width: 30px;
    min-height: 30px;
}
QPushButton#ctrl_btn:hover { color: #FFFFFF; }

QPushButton#play_btn {
    background-color: #FFFFFF;
    color: #000000;
    border: none;
    font-size: 16px;
    border-radius: 18px;
    min-width: 36px;
    max-width: 36px;
    min-height: 36px;
    max-height: 36px;
    font-weight: bold;
}
QPushButton#play_btn:hover   { background-color: #DDDDDD; }
QPushButton#play_btn:pressed { background-color: #BBBBBB; }

/* Secondary buttons (shuffle, repeat) */
QPushButton#secondary_btn {
    background-color: transparent;
    color: #666666;
    border: none;
    font-size: 14px;
    padding: 4px 6px;
    border-radius: 4px;
    min-width: 28px; min-height: 28px;
}
QPushButton#secondary_btn:hover { color: #FFFFFF; }
QPushButton#secondary_btn:checked { color: #FFFFFF; }

/* Empty state */
#empty_label {
    color: #FFFFFF;
    font-size: 14px;
}

/* ── Sidebar usuario / logout ───────────────────── */
#sidebar_user_label {
    color: #555555;
    font-size: 11px;
    font-weight: 400;
    padding: 0 4px;
}

QPushButton#logout_btn {
    background-color: transparent;
    color: #888888;
    text-align: left;
    padding: 7px 10px;
    border: none;
    border-radius: 5px;
    font-size: 13px;
    font-weight: 600;
}
QPushButton#logout_btn:hover { background-color: #1A1A1A; color: #FF4444; }

/* ── Auth ────────────────────────────────────────── */
#auth_window, #auth_card {
    background-color: #000000;
}

#auth_titlebar {
    background-color: #000000;
    border-bottom: 1px solid #111111;
}

#auth_title {
    font-size: 26px;
    font-weight: bold;
    color: #FFFFFF;
}

#auth_subtitle {
    font-size: 12px;
    font-weight: 400;
    color: #666666;
}

#auth_hint {
    font-size: 12px;
    font-weight: 400;
    color: #555555;
}

#auth_field_label {
    font-size: 10px;
    font-weight: bold;
    color: #666666;
    letter-spacing: 1.5px;
}

QLineEdit#auth_input {
    background-color: transparent;
    color: #FFFFFF;
    border: none;
    border-bottom: 1px solid #2A2A2A;
    border-radius: 0;
    padding: 6px 0;
    font-size: 14px;
    font-weight: 600;
    selection-background-color: #333333;
}

QLineEdit#auth_input:focus {
    border-bottom: 1px solid #FFFFFF;
}

QPushButton#auth_primary_btn {
    background-color: #FFFFFF;
    color: #000000;
    border: none;
    border-radius: 6px;
    font-size: 14px;
    font-weight: bold;
}

QPushButton#auth_primary_btn:hover {
    background-color: #E0E0E0;
}

QPushButton#auth_primary_btn:pressed {
    background-color: #BBBBBB;
}

QPushButton#auth_link_btn {
    background-color: transparent;
    color: #FFFFFF;
    border: none;
    font-size: 12px;
    font-weight: bold;
    padding: 0;
    text-decoration: underline;
}

QPushButton#auth_link_btn:hover {
    color: #AAAAAA;
}

QPushButton#auth_toggle_btn {
    background-color: transparent;
    color: #555555;
    border: none;
    border-bottom: 1px solid #2A2A2A;
    border-radius: 0;
    font-size: 11px;
    font-weight: 400;
    padding: 6px 8px;
}

QPushButton#auth_toggle_btn:hover {
    color: #FFFFFF;
}

#auth_error {
    font-size: 12px;
    color: #FF4444;
}
"""
