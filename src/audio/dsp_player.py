import threading
import numpy as np
import sounddevice as sd
from pedalboard import Pedalboard, Reverb, Compressor
from pedalboard.io import AudioFile
from PyQt6.QtCore import QObject, pyqtSignal, QTimer
from PyQt6.QtMultimedia import QMediaPlayer

from src.audio.dsd_decoder import is_dsd, decode_dsd_to_wav

_CROSSFADE_S = 3.0
_BLOCKSIZE   = 2048


class DSPPlayer(QObject):
    position_changed = pyqtSignal(int)
    duration_changed = pyqtSignal(int)
    state_changed    = pyqtSignal(QMediaPlayer.PlaybackState)
    track_finished   = pyqtSignal()
    error_occurred   = pyqtSignal(str)
    crossfade_started = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._lock = threading.Lock()

        # Audio data: (frames, channels) float32
        self._data:       np.ndarray | None = None
        self._samplerate: int = 44100
        self._pos:        int = 0          # frame index

        # Crossfade data
        self._cf_data:          np.ndarray | None = None
        self._cf_samplerate:    int  = 44100
        self._cf_pos:           int  = 0
        self._cf_total_frames:  int  = 0
        self._cf_done_frames:   int  = 0
        self._cf_active:        bool = False
        self._cf_just_done:     bool = False

        # State
        self._playing:       bool = False
        self._finished_flag: bool = False
        self._state = QMediaPlayer.PlaybackState.StoppedState
        self._volume:  float = 0.8
        self._rg:      float = 1.0

        # Effects
        self._board:         Pedalboard = Pedalboard([])
        self._pending_board: Pedalboard | None = None
        self._stereo_width:  float = 1.0  # 1.0 = normal, >1 más ancho

        # Sounddevice stream
        self._stream: sd.OutputStream | None = None

        # Timer para emitir señales desde el hilo principal
        self._timer = QTimer(self)
        self._timer.setInterval(80)
        self._timer.timeout.connect(self._tick)
        self._timer.start()

    # ── Carga ────────────────────────────────────────────────

    def load(self, filepath: str):
        self.cancel_crossfade()
        try:
            path = self._resolve_path(filepath)
            if path is None:
                return
            data, sr = self._read_audio(path)
            with self._lock:
                self._data       = data
                self._samplerate = sr
                self._pos        = 0
                self._playing    = False
                self._finished_flag = False
            self.duration_changed.emit(self._frames_to_ms(len(data), sr))
            self._set_state(QMediaPlayer.PlaybackState.StoppedState)
            self._reopen_stream(sr, data.shape[1])
        except Exception as e:
            self.error_occurred.emit(str(e))

    def _resolve_path(self, filepath: str) -> str | None:
        if is_dsd(filepath):
            tmp = decode_dsd_to_wav(filepath)
            if tmp:
                return tmp
            self.error_occurred.emit('No se pudo decodificar el archivo DSD.')
            return None
        return filepath

    def _read_audio(self, filepath: str) -> tuple[np.ndarray, int]:
        with AudioFile(filepath) as f:
            data = f.read(f.frames)  # (channels, frames)
            sr   = int(f.samplerate)
        data = data.T.astype('float32')   # → (frames, channels)
        if data.ndim == 1:
            data = data[:, np.newaxis]
        if data.shape[1] == 1:            # mono → stereo
            data = np.repeat(data, 2, axis=1)
        return data, sr

    def _reopen_stream(self, sr: int, channels: int):
        if self._stream is not None:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception:
                pass
        self._stream = sd.OutputStream(
            samplerate=sr,
            channels=channels,
            dtype='float32',
            blocksize=_BLOCKSIZE,
            callback=self._audio_callback,
        )
        self._stream.start()

    # ── Callback de audio (hilo de sounddevice) ───────────────

    def _audio_callback(self, outdata: np.ndarray, frames: int, time, status):
        # Intercambiar board si la UI envió uno nuevo
        if self._pending_board is not None:
            self._board         = self._pending_board
            self._pending_board = None

        with self._lock:
            if not self._playing or self._data is None:
                outdata[:] = 0
                return

            n  = len(self._data)
            ch = self._data.shape[1]

            # Chunk del track actual
            start    = self._pos
            end      = min(start + frames, n)
            avail    = end - start
            chunk    = np.zeros((frames, ch), dtype='float32')
            if avail > 0:
                chunk[:avail] = self._data[start:end]

            # Crossfade
            if self._cf_active and self._cf_data is not None:
                cf_n     = len(self._cf_data)
                cf_start = self._cf_pos
                cf_end   = min(cf_start + frames, cf_n)
                cf_avail = cf_end - cf_start
                cf_chunk = np.zeros((frames, ch), dtype='float32')
                if cf_avail > 0:
                    raw = self._cf_data[cf_start:cf_end]
                    if raw.shape[1] != ch:
                        raw = np.repeat(raw[:, :1], ch, axis=1)
                    cf_chunk[:cf_avail] = raw

                total  = max(self._cf_total_frames, 1)
                done   = self._cf_done_frames
                ratios = np.linspace(done / total,
                                     min(1.0, (done + frames) / total),
                                     frames, dtype='float32')
                fi = ratios[:, np.newaxis]
                fo = 1.0 - fi
                chunk = chunk * fo + cf_chunk * fi

                self._cf_pos         += frames
                self._cf_done_frames += frames
                self._pos             = end

                if self._cf_done_frames >= self._cf_total_frames:
                    self._data        = self._cf_data
                    self._samplerate  = self._cf_samplerate
                    self._pos         = self._cf_pos
                    self._cf_data     = None
                    self._cf_active   = False
                    self._cf_just_done = True
            else:
                self._pos = end
                if avail < frames:
                    self._finished_flag = True

        # Efectos pedalboard
        if len(self._board) > 0:
            try:
                proc = self._board(chunk.T, self._samplerate)
                proc = proc[:, :frames] if proc.shape[1] >= frames else np.pad(proc, ((0,0),(0, frames - proc.shape[1])))
                chunk = proc.T.astype('float32')
            except Exception:
                pass

        # Amplitud estéreo (mid-side)
        w = self._stereo_width
        if w != 1.0 and chunk.shape[1] >= 2:
            mid  = (chunk[:, 0] + chunk[:, 1]) * 0.5
            side = (chunk[:, 0] - chunk[:, 1]) * 0.5 * w
            chunk[:, 0] = mid + side
            chunk[:, 1] = mid - side

        vol = self._volume * self._rg
        out = (chunk * vol).astype('float32')
        if out.shape[0] < frames:
            out = np.vstack([out, np.zeros((frames - out.shape[0], out.shape[1]), dtype='float32')])
        outdata[:] = out[:frames]

    # ── Timer (hilo principal) ────────────────────────────────

    def _tick(self):
        if self._cf_just_done:
            self._cf_just_done = False
            if self._data is not None:
                self.duration_changed.emit(self._frames_to_ms(len(self._data), self._samplerate))
            self.crossfade_started.emit()

        if self._finished_flag:
            self._finished_flag = False
            self._playing = False
            self._set_state(QMediaPlayer.PlaybackState.StoppedState)
            self.track_finished.emit()

        if self._playing and self._data is not None:
            self.position_changed.emit(self.position)

    # ── API pública ───────────────────────────────────────────

    def play(self):
        with self._lock:
            self._playing       = True
            self._finished_flag = False
        self._set_state(QMediaPlayer.PlaybackState.PlayingState)

    def pause(self):
        with self._lock:
            self._playing = False
        self._set_state(QMediaPlayer.PlaybackState.PausedState)

    def toggle(self):
        if self.is_playing:
            self.pause()
        else:
            self.play()

    def stop(self):
        with self._lock:
            self._playing = False
            self._pos     = 0
        self._set_state(QMediaPlayer.PlaybackState.StoppedState)

    def seek(self, ms: int):
        if self._data is None:
            return
        frame = int(ms / 1000 * self._samplerate)
        with self._lock:
            self._pos = max(0, min(frame, len(self._data) - 1))

    def set_volume(self, value: int):
        self._volume = value / 100.0

    def set_replaygain(self, gain_db):
        if gain_db is not None:
            self._rg = max(0.25, min(3.0, 10 ** (gain_db / 20.0)))
        else:
            self._rg = 1.0

    def begin_crossfade(self, filepath: str):
        if self._cf_active:
            return
        try:
            path = self._resolve_path(filepath)
            if path is None:
                return
            data, sr = self._read_audio(path)
            cf_frames = int(_CROSSFADE_S * self._samplerate)
            with self._lock:
                self._cf_data         = data
                self._cf_samplerate   = sr
                self._cf_pos          = 0
                self._cf_total_frames = cf_frames
                self._cf_done_frames  = 0
                self._cf_active       = True
            self.crossfade_started.emit()
        except Exception as e:
            self.error_occurred.emit(str(e))

    def cancel_crossfade(self):
        with self._lock:
            self._cf_active = False
            self._cf_data   = None
            self._cf_pos    = 0

    def update_effects(self, enabled: bool, room: float, mix: float, width: float):
        """Actualiza la cadena de efectos desde la UI (hilo principal)."""
        if enabled:
            board = Pedalboard([
                Compressor(threshold_db=-18, ratio=2.5, attack_ms=10, release_ms=100),
                Reverb(room_size=room, damping=0.5, wet_level=mix, dry_level=1.0 - mix * 0.5),
            ])
        else:
            board = Pedalboard([])
        self._pending_board  = board
        self._stereo_width   = width if enabled else 1.0

    # ── Propiedades ───────────────────────────────────────────

    @property
    def is_playing(self) -> bool:
        return self._playing

    @property
    def position(self) -> int:
        if self._data is None:
            return 0
        return self._frames_to_ms(self._pos, self._samplerate)

    @property
    def duration(self) -> int:
        if self._data is None:
            return 0
        return self._frames_to_ms(len(self._data), self._samplerate)

    # ── Helpers ───────────────────────────────────────────────

    @staticmethod
    def _frames_to_ms(frames: int, sr: int) -> int:
        return int(frames / sr * 1000) if sr > 0 else 0

    def _set_state(self, state):
        self._state = state
        self.state_changed.emit(state)
