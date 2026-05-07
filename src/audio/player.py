import os
from typing import Optional
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtCore import QUrl, QObject, pyqtSignal, QTimer

from src.audio.dsd_decoder import is_dsd, decode_dsd_to_wav

_CROSSFADE_DURATION_MS = 3000
_CROSSFADE_STEPS = 50
_CROSSFADE_INTERVAL_MS = _CROSSFADE_DURATION_MS // _CROSSFADE_STEPS  # 60ms


class AudioPlayer(QObject):
    position_changed = pyqtSignal(int)
    duration_changed = pyqtSignal(int)
    state_changed = pyqtSignal(QMediaPlayer.PlaybackState)
    track_finished = pyqtSignal()
    error_occurred = pyqtSignal(str)
    crossfade_started = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        # Dos players alternos; _active indica cuál está en uso
        self._players: list[QMediaPlayer] = []
        self._outputs: list[QAudioOutput] = []
        self._tmp_wavs: list[Optional[str]] = [None, None]
        self._active: int = 0

        for i in range(2):
            out = QAudioOutput()
            out.setVolume(0.8)
            pl = QMediaPlayer()
            pl.setAudioOutput(out)
            self._players.append(pl)
            self._outputs.append(out)

        # Volumen de usuario (0-100 → 0.0-1.0) y multiplicador ReplayGain
        self._user_volume: float = 0.8
        self._rg_multiplier: float = 1.0

        # Estado crossfade
        self._crossfading: bool = False
        self._cf_timer: Optional[QTimer] = None
        self._cf_step: int = 0
        self._cf_vol_out: float = 0.0   # volumen inicial del player saliente
        self._cf_inactive: int = 1       # índice del player entrante durante fade

        # Routing de señales: solo el player activo emite hacia fuera
        for i in range(2):
            self._players[i].positionChanged.connect(
                lambda pos, idx=i: self.position_changed.emit(int(pos)) if idx == self._active else None
            )
            self._players[i].durationChanged.connect(
                lambda dur, idx=i: self.duration_changed.emit(int(dur)) if idx == self._active else None
            )
            self._players[i].playbackStateChanged.connect(
                lambda state, idx=i: self.state_changed.emit(state) if idx == self._active else None
            )
            self._players[i].mediaStatusChanged.connect(
                lambda status, idx=i: self._on_media_status(status, idx)
            )
            self._players[i].errorOccurred.connect(
                lambda error, error_str, idx=i: self._on_error(error, error_str, idx)
            )

    # ── API pública ───────────────────────────────────────────

    def load(self, filepath: str):
        """Carga una pista en el player activo, cancelando cualquier crossfade en curso."""
        self.cancel_crossfade()
        self._cleanup_tmp(self._active)

        if is_dsd(filepath):
            tmp = decode_dsd_to_wav(filepath)
            if tmp:
                self._tmp_wavs[self._active] = tmp
                self._players[self._active].setSource(QUrl.fromLocalFile(tmp))
            else:
                self.error_occurred.emit(
                    'No se pudo decodificar el archivo DSD. '
                    'Asegúrate de que FFmpeg está instalado.'
                )
        else:
            self._players[self._active].setSource(QUrl.fromLocalFile(filepath))

    def play(self):
        self._players[self._active].play()

    def pause(self):
        self._players[self._active].pause()

    def toggle(self):
        if self.is_playing:
            self.pause()
        else:
            self.play()

    def stop(self):
        self._players[self._active].stop()

    def seek(self, position_ms: int):
        self._players[self._active].setPosition(position_ms)

    def set_volume(self, value: int):
        self._user_volume = value / 100.0
        self._apply_volume(self._active)

    def set_replaygain(self, gain_db: Optional[float]):
        """Calcula y aplica el multiplicador ReplayGain al output activo."""
        if gain_db is not None:
            multiplier = 10 ** (gain_db / 20.0)
            self._rg_multiplier = max(0.25, min(3.0, multiplier))
        else:
            self._rg_multiplier = 1.0
        self._apply_volume(self._active)

    @property
    def is_playing(self) -> bool:
        return self._players[self._active].playbackState() == QMediaPlayer.PlaybackState.PlayingState

    @property
    def position(self) -> int:
        return self._players[self._active].position()

    @property
    def duration(self) -> int:
        return self._players[self._active].duration()

    # ── Crossfade ─────────────────────────────────────────────

    def begin_crossfade(self, filepath: str):
        """Carga la siguiente pista en el player inactivo e inicia el fade cruzado."""
        if self._crossfading:
            return

        inactive = 1 - self._active
        self._cf_inactive = inactive
        self._cleanup_tmp(inactive)

        # Cargar nueva pista en player inactivo a volumen 0
        self._outputs[inactive].setVolume(0.0)
        if is_dsd(filepath):
            tmp = decode_dsd_to_wav(filepath)
            if tmp:
                self._tmp_wavs[inactive] = tmp
                self._players[inactive].setSource(QUrl.fromLocalFile(tmp))
            else:
                return
        else:
            self._players[inactive].setSource(QUrl.fromLocalFile(filepath))

        self._players[inactive].play()

        # Iniciar fade
        self._crossfading = True
        self._cf_step = 0
        self._cf_vol_out = self._outputs[self._active].volume()

        self._cf_timer = QTimer(self)
        self._cf_timer.setInterval(_CROSSFADE_INTERVAL_MS)
        self._cf_timer.timeout.connect(self._crossfade_tick)
        self._cf_timer.start()

        self.crossfade_started.emit()

    def cancel_crossfade(self):
        """Cancela un crossfade en curso y restaura el estado."""
        if not self._crossfading:
            return
        if self._cf_timer:
            self._cf_timer.stop()
            self._cf_timer.deleteLater()
            self._cf_timer = None

        inactive = self._cf_inactive
        self._players[inactive].stop()
        self._cleanup_tmp(inactive)
        # Restaurar volumen del player activo
        self._apply_volume(self._active)
        self._crossfading = False

    # ── Interno ──────────────────────────────────────────────

    def _crossfade_tick(self):
        self._cf_step += 1
        ratio = self._cf_step / _CROSSFADE_STEPS  # 0.0 → 1.0

        inactive = self._cf_inactive
        # Fade out del player activo
        vol_out = self._cf_vol_out * (1.0 - ratio)
        self._outputs[self._active].setVolume(max(0.0, vol_out))
        # Fade in del player inactivo
        vol_in = self._user_volume * self._rg_multiplier * ratio
        self._outputs[inactive].setVolume(min(self._user_volume * self._rg_multiplier, vol_in))

        if self._cf_step >= _CROSSFADE_STEPS:
            # Crossfade completado
            self._cf_timer.stop()
            self._cf_timer.deleteLater()
            self._cf_timer = None

            # Parar player saliente y limpiar su tmp_wav
            old_active = self._active
            self._players[old_active].stop()
            self._cleanup_tmp(old_active)

            # El player inactivo pasa a ser el activo
            self._active = inactive
            self._apply_volume(self._active)
            self._crossfading = False

    def _on_media_status(self, status, player_idx: int):
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            if player_idx != self._active:
                return  # ignorar eventos del player inactivo
            if self._crossfading:
                return  # el crossfade ya gestiona la transición
            self._cleanup_tmp(player_idx)
            self.track_finished.emit()

    def _on_error(self, error, error_str: str, player_idx: int):
        if player_idx == self._active:
            self.error_occurred.emit(error_str)

    def _apply_volume(self, player_idx: int):
        vol = min(1.0, self._user_volume * self._rg_multiplier)
        self._outputs[player_idx].setVolume(vol)

    def _cleanup_tmp(self, player_idx: int):
        tmp = self._tmp_wavs[player_idx]
        if tmp and os.path.isfile(tmp):
            try:
                os.unlink(tmp)
            except Exception:
                pass
        self._tmp_wavs[player_idx] = None
