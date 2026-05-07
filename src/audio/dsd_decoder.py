import subprocess
import shutil
import tempfile
import os
from typing import Optional


DSD_EXTENSIONS = {'.dsf', '.dff'}


def is_dsd(filepath: str) -> bool:
    return os.path.splitext(filepath)[1].lower() in DSD_EXTENSIONS


def ffmpeg_path() -> Optional[str]:
    path = shutil.which('ffmpeg')
    if path:
        return path
    # Rutas habituales de instalación con winget/gyan
    import glob
    candidates = [
        r'C:\Program Files\ffmpeg\bin\ffmpeg.exe',
        r'C:\ffmpeg\bin\ffmpeg.exe',
    ]
    # Ruta de instalación winget (Gyan.FFmpeg)
    winget_base = os.path.join(os.environ.get('LOCALAPPDATA', ''),
                               'Microsoft', 'WinGet', 'Packages')
    for match in glob.glob(os.path.join(winget_base, 'Gyan.FFmpeg*', '**', 'ffmpeg.exe'),
                           recursive=True):
        candidates.insert(0, match)
    for c in candidates:
        if os.path.isfile(c):
            return c
    return None


def decode_dsd_to_wav(filepath: str) -> Optional[str]:
    """
    Decodifica un archivo DSD a WAV temporal (PCM 32-bit float, 352.8 kHz).
    Devuelve la ruta del archivo temporal, o None si falla.
    El caller es responsable de eliminar el archivo temporal cuando termine.
    """
    ffmpeg = ffmpeg_path()
    if not ffmpeg:
        return None

    tmp = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
    tmp.close()

    cmd = [
        ffmpeg,
        '-y',
        '-i', filepath,
        '-acodec', 'pcm_f32le',
        '-ar', '352800',
        tmp.name
    ]

    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=60
        )
        if result.returncode == 0:
            return tmp.name
    except Exception:
        pass

    try:
        os.unlink(tmp.name)
    except Exception:
        pass
    return None
