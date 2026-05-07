import os
import random
from typing import List, Dict, Optional
from PyQt6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
                              QFileDialog, QLabel, QSizePolicy, QMessageBox)
from PyQt6.QtCore import QThread, QObject, pyqtSignal, Qt


from src.audio.scanner import Track, scan_folder
from src.audio.player import AudioPlayer
from src.ui.sidebar import Sidebar
from src.ui.track_list import TrackList
from src.ui.player_bar import PlayerBar
from src.ui.title_bar import TitleBar
from src.ui.styles import STYLESHEET
from src.utils.config import load_folders, save_folders

_CROSSFADE_THRESHOLD_MS = 3000  # ms antes del fin en que se activa el crossfade


class _ScanWorker(QObject):
    finished = pyqtSignal(str, list)  # folder_path, tracks

    def __init__(self, folder_path: str):
        super().__init__()
        self._folder = folder_path

    def run(self):
        tracks = scan_folder(self._folder)
        self.finished.emit(self._folder, tracks)


class MainWindow(QMainWindow):
    logout_requested = pyqtSignal()

    def __init__(self, email: str = ''):
        super().__init__()
        self._email = email
        self.setWindowTitle('Spotify Skip Permissions')
        self.setMinimumSize(900, 600)
        self.resize(1200, 700)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)

        self._folder_tracks: Dict[str, List[Track]] = {}
        self._current_tracks: List[Track] = []
        self._playing_index: int = -1
        self._current_folder: Optional[str] = None  # None = all songs
        self._scan_threads: List[QThread] = []
        self._scan_workers: List[_ScanWorker] = []

        # ── Shuffle / Repeat ──────────────────────────────────
        self._shuffle: bool = False
        self._shuffle_order: List[int] = []
        self._repeat_mode: int = 0  # 0=off, 1=all, 2=one

        # ── Crossfade state ──────────────────────────────────
        self._crossfade_triggered: bool = False
        self._pending_cf_index: int = -1

        self.setStyleSheet(STYLESHEET)

        # ── Root layout ──────────────────────────────────────
        root_widget = QWidget()
        root_layout = QVBoxLayout(root_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        root_layout.addWidget(TitleBar(self))

        # Main content area (sidebar + tracklist)
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        self._sidebar = Sidebar()
        self._sidebar.all_songs_requested.connect(self._show_all_songs)
        self._sidebar.folder_selected.connect(self._show_folder)
        self._sidebar.add_folder_requested.connect(self._add_folder)
        self._sidebar.logout_requested.connect(self.logout_requested)
        if self._email:
            self._sidebar.set_user(self._email)

        self._track_list = TrackList()
        self._track_list.track_activated.connect(self._on_track_activated)

        content_layout.addWidget(self._sidebar)
        content_layout.addWidget(self._track_list)

        # Player bar
        self._player_bar = PlayerBar()
        self._player_bar.play_pause_clicked.connect(self._on_play_pause)
        self._player_bar.prev_clicked.connect(self._on_prev)
        self._player_bar.next_clicked.connect(self._on_next)
        self._player_bar.seek_requested.connect(self._on_seek)
        self._player_bar.volume_changed.connect(self._on_volume_changed)
        self._player_bar.shuffle_toggled.connect(self._on_shuffle_toggled)
        self._player_bar.repeat_clicked.connect(self._on_repeat_clicked)

        root_layout.addWidget(content_widget)
        root_layout.addWidget(self._player_bar)
        self.setCentralWidget(root_widget)

        # ── Audio player ─────────────────────────────────────
        self._player = AudioPlayer(self)
        self._player.position_changed.connect(self._on_position_changed)
        self._player.duration_changed.connect(self._player_bar.set_duration)
        self._player.state_changed.connect(self._on_state_changed)
        self._player.track_finished.connect(self._on_track_finished)
        self._player.error_occurred.connect(self._on_player_error)
        self._player.crossfade_started.connect(self._on_crossfade_started)

        # Load saved folders
        for folder in load_folders():
            if os.path.isdir(folder):
                self._start_scan(folder)

    # ── Folder management ────────────────────────────────────

    def _add_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self, 'Seleccionar carpeta de música',
            os.path.expanduser('~\\Music'))
        if folder and folder not in self._folder_tracks:
            self._start_scan(folder)

    def _start_scan(self, folder_path: str):
        self._sidebar.add_folder(folder_path)
        self._folder_tracks[folder_path] = []

        worker = _ScanWorker(folder_path)
        thread = QThread()
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.finished.connect(self._on_scan_finished)
        worker.finished.connect(thread.quit)
        thread.finished.connect(thread.deleteLater)
        self._scan_threads.append(thread)
        self._scan_workers.append(worker)
        thread.start()

    def _on_scan_finished(self, folder_path: str, tracks: List[Track]):
        self._folder_tracks[folder_path] = tracks
        self._refresh_current_view()
        self._save_folders()

    def _save_folders(self):
        save_folders(list(self._folder_tracks.keys()))

    # ── View management ──────────────────────────────────────

    def _show_all_songs(self):
        self._current_folder = None
        self._track_list.set_header('Todas las canciones')
        all_tracks = []
        for tracks in self._folder_tracks.values():
            all_tracks.extend(tracks)
        self._current_tracks = all_tracks
        self._track_list.set_tracks(self._current_tracks)
        self._update_playing_row()

    def _show_folder(self, folder_path: str):
        self._current_folder = folder_path
        name = os.path.basename(folder_path) or folder_path
        self._track_list.set_header(name)
        self._current_tracks = self._folder_tracks.get(folder_path, [])
        self._track_list.set_tracks(self._current_tracks)
        self._update_playing_row()

    def _refresh_current_view(self):
        if self._current_folder is None:
            self._show_all_songs()
        else:
            self._show_folder(self._current_folder)

    def _update_playing_row(self):
        if self._playing_index >= 0:
            playing_track = self._get_playing_track()
            if playing_track:
                row = self._track_list.find_track_row(playing_track)
                self._track_list.set_playing_row(row)

    # ── Shuffle / Repeat ─────────────────────────────────────

    def _on_shuffle_toggled(self, enabled: bool):
        self._shuffle = enabled
        if enabled:
            self._rebuild_shuffle_order()

    def _on_repeat_clicked(self):
        self._repeat_mode = (self._repeat_mode + 1) % 3
        self._player_bar.set_repeat_mode(self._repeat_mode)

    def _rebuild_shuffle_order(self):
        """Genera un orden aleatorio para todas las pistas, poniendo la actual primero."""
        n = len(self._current_tracks)
        if n == 0:
            self._shuffle_order = []
            return
        indices = list(range(n))
        if 0 <= self._playing_index < n:
            indices.remove(self._playing_index)
            random.shuffle(indices)
            self._shuffle_order = [self._playing_index] + indices
        else:
            random.shuffle(indices)
            self._shuffle_order = indices

    def _get_next_index(self) -> int:
        """Devuelve el índice de la siguiente pista según shuffle y repeat."""
        n = len(self._current_tracks)
        if n == 0:
            return -1

        if self._repeat_mode == 2:  # repeat one
            return self._playing_index

        if self._shuffle:
            if not self._shuffle_order:
                self._rebuild_shuffle_order()
            try:
                pos = self._shuffle_order.index(self._playing_index)
            except ValueError:
                pos = -1
            next_pos = pos + 1
            if next_pos >= len(self._shuffle_order):
                if self._repeat_mode == 1:  # repeat all
                    self._rebuild_shuffle_order()
                    return self._shuffle_order[0] if self._shuffle_order else -1
                return -1
            return self._shuffle_order[next_pos]
        else:
            next_idx = self._playing_index + 1
            if next_idx >= n:
                if self._repeat_mode == 1:  # repeat all
                    return 0
                return -1
            return next_idx

    def _get_prev_index(self) -> int:
        """Devuelve el índice de la pista anterior según shuffle y repeat."""
        n = len(self._current_tracks)
        if n == 0:
            return -1

        if self._repeat_mode == 2:  # repeat one
            return self._playing_index

        if self._shuffle:
            if not self._shuffle_order:
                self._rebuild_shuffle_order()
            try:
                pos = self._shuffle_order.index(self._playing_index)
            except ValueError:
                pos = 0
            prev_pos = pos - 1
            if prev_pos < 0:
                if self._repeat_mode == 1:
                    return self._shuffle_order[-1] if self._shuffle_order else -1
                return 0
            return self._shuffle_order[prev_pos]
        else:
            prev_idx = self._playing_index - 1
            if prev_idx < 0:
                if self._repeat_mode == 1:
                    return n - 1
                return 0
            return prev_idx

    # ── Playback ─────────────────────────────────────────────

    def _on_track_activated(self, track: Track, index: int):
        self._player.cancel_crossfade()
        self._playing_index = index
        if self._shuffle:
            self._rebuild_shuffle_order()
        self._play_track(track)

    def _play_track(self, track: Track):
        self._crossfade_triggered = False
        self._player.load(track.path)
        self._player.set_replaygain(track.replaygain)
        self._player.play()
        self._player_bar.set_track(track)
        row = self._track_list.find_track_row(track)
        self._track_list.set_playing_row(row)

    def _get_playing_track(self) -> Optional[Track]:
        if 0 <= self._playing_index < len(self._current_tracks):
            return self._current_tracks[self._playing_index]
        return None

    def _on_play_pause(self):
        if self._playing_index < 0 and self._current_tracks:
            self._playing_index = 0
            if self._shuffle:
                self._rebuild_shuffle_order()
            self._play_track(self._current_tracks[0])
        else:
            self._player.toggle()

    def _on_prev(self):
        if not self._current_tracks:
            return
        # Si llevamos más de 3 segundos reproducidos, volver al inicio
        if self._player.position > 3000:
            self._player.cancel_crossfade()
            self._player.seek(0)
            return
        self._player.cancel_crossfade()
        prev_index = self._get_prev_index()
        if prev_index < 0:
            self._player.seek(0)
            return
        self._playing_index = prev_index
        self._play_track(self._current_tracks[prev_index])

    def _on_next(self):
        if not self._current_tracks:
            return
        self._player.cancel_crossfade()
        next_index = self._get_next_index()
        if next_index < 0:
            self._player.stop()
            self._player_bar.set_playing(False)
            return
        self._playing_index = next_index
        self._play_track(self._current_tracks[next_index])

    def _on_track_finished(self):
        """Llamado cuando termina la pista (sin crossfade)."""
        self._on_next()

    def _on_seek(self, ms: int):
        self._player.seek(ms)

    def _on_volume_changed(self, value: int):
        self._player.set_volume(value)

    def _on_position_changed(self, ms: int):
        """Gestiona la posición: actualiza la barra e inicia crossfade si toca."""
        self._player_bar.set_position(ms)

        duration = self._player.duration
        if (
            duration > 0
            and not self._crossfade_triggered
            and ms > 0
            and duration - ms <= _CROSSFADE_THRESHOLD_MS
        ):
            next_index = self._get_next_index()
            if next_index >= 0:
                self._pending_cf_index = next_index
                self._crossfade_triggered = True
                self._player.begin_crossfade(self._current_tracks[next_index].path)

    def _on_crossfade_started(self):
        """Al comenzar el crossfade, actualizar la UI con la nueva pista."""
        if self._pending_cf_index < 0:
            return
        self._playing_index = self._pending_cf_index
        self._pending_cf_index = -1
        track = self._get_playing_track()
        if track:
            self._player_bar.set_track(track)
            row = self._track_list.find_track_row(track)
            self._track_list.set_playing_row(row)
            # Aplicar ReplayGain de la nueva pista al player inactivo (que ahora está en fade-in)
            # Se aplica después del crossfade cuando el player inactivo se vuelve activo

    def _on_state_changed(self, state):
        from PyQt6.QtMultimedia import QMediaPlayer
        self._player_bar.set_playing(state == QMediaPlayer.PlaybackState.PlayingState)

    def _on_player_error(self, error_str: str):
        if error_str:
            QMessageBox.warning(self, 'Error de reproducción',
                                f'No se pudo reproducir el archivo.\n{error_str}')
