import os
from dataclasses import dataclass, field
from typing import Optional, List
from mutagen import File as MutagenFile

SUPPORTED_EXTENSIONS = {'.mp3', '.flac', '.wav', '.m4a', '.dsf', '.dff', '.aiff', '.aif'}


@dataclass
class Track:
    path: str
    title: str = ""
    artist: str = ""
    album: str = ""
    duration: float = 0.0
    fmt: str = ""
    cover_data: Optional[bytes] = field(default=None, repr=False)
    replaygain: Optional[float] = None

    @property
    def duration_str(self) -> str:
        if self.duration <= 0:
            return "--:--"
        total = int(self.duration)
        return f"{total // 60}:{total % 60:02d}"


def scan_folder(folder_path: str) -> List[Track]:
    tracks = []
    for root, dirs, files in os.walk(folder_path):
        dirs.sort()
        for filename in sorted(files):
            ext = os.path.splitext(filename)[1].lower()
            if ext in SUPPORTED_EXTENSIONS:
                tracks.append(read_metadata(os.path.join(root, filename)))
    return tracks


def read_metadata(filepath: str) -> Track:
    ext = os.path.splitext(filepath)[1].lower()
    basename = os.path.splitext(os.path.basename(filepath))[0]
    track = Track(path=filepath, title=basename, fmt=ext.upper().lstrip('.'))

    try:
        audio = MutagenFile(filepath, easy=True)
        if audio is None:
            return track

        tags = audio.tags
        if tags:
            track.title = str(tags.get('title', [basename])[0]) or basename
            track.artist = str(tags.get('artist', [''])[0])
            track.album = str(tags.get('album', [''])[0])

        if hasattr(audio, 'info') and audio.info:
            track.duration = getattr(audio.info, 'length', 0.0)

        track.cover_data = _extract_cover(filepath, ext)
        track.replaygain = _read_replaygain(filepath, ext)
    except Exception:
        pass

    return track


def _read_replaygain(filepath: str, ext: str) -> Optional[float]:
    """Lee el valor ReplayGain Track Gain en dB desde los metadatos del archivo."""
    try:
        if ext == '.mp3':
            from mutagen.id3 import ID3
            tags = ID3(filepath)
            for key in tags.keys():
                if key.startswith('TXXX'):
                    frame = tags[key]
                    if hasattr(frame, 'desc') and frame.desc.upper() == 'REPLAYGAIN_TRACK_GAIN':
                        text = str(frame.text[0]) if frame.text else ''
                        return _parse_gain(text)
        elif ext in ('.flac', '.ogg'):
            audio = MutagenFile(filepath, easy=False)
            if audio and audio.tags:
                tag = audio.tags.get('replaygain_track_gain')
                if tag:
                    val = str(tag[0]) if isinstance(tag, list) else str(tag)
                    return _parse_gain(val)
        elif ext == '.m4a':
            from mutagen.mp4 import MP4
            audio = MP4(filepath)
            if audio.tags:
                key = '----:com.apple.iTunes:REPLAYGAIN_TRACK_GAIN'
                tag = audio.tags.get(key)
                if tag:
                    val = tag[0].decode('utf-8') if isinstance(tag[0], bytes) else str(tag[0])
                    return _parse_gain(val)
    except Exception:
        pass
    return None


def _parse_gain(text: str) -> Optional[float]:
    """Convierte un texto como '-6.5 dB' o '+2.1 dB' a float."""
    try:
        cleaned = text.strip().lower().replace('db', '').strip()
        return float(cleaned)
    except (ValueError, AttributeError):
        return None


def _extract_cover(filepath: str, ext: str) -> Optional[bytes]:
    try:
        if ext == '.mp3':
            from mutagen.id3 import ID3
            tags = ID3(filepath)
            for key in tags.keys():
                if key.startswith('APIC'):
                    return tags[key].data
        elif ext == '.flac':
            from mutagen.flac import FLAC
            audio = FLAC(filepath)
            if audio.pictures:
                return audio.pictures[0].data
        elif ext in ('.m4a', '.alac'):
            from mutagen.mp4 import MP4
            audio = MP4(filepath)
            if audio.tags and 'covr' in audio.tags:
                return bytes(audio.tags['covr'][0])
    except Exception:
        pass
    return None
