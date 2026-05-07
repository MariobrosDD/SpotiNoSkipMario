import io
from typing import Optional
from PIL import Image
from PyQt6.QtGui import QPixmap, QColor, QPainter, QFont
from PyQt6.QtCore import Qt


def bytes_to_pixmap(data: bytes, grayscale: bool = False) -> Optional[QPixmap]:
    try:
        img = Image.open(io.BytesIO(data))
        if grayscale:
            img = img.convert('L').convert('RGB')
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        pixmap = QPixmap()
        pixmap.loadFromData(buf.getvalue())
        return pixmap
    except Exception:
        return None


def placeholder_pixmap(size: int = 56) -> QPixmap:
    pixmap = QPixmap(size, size)
    pixmap.fill(QColor('#1A1A1A'))
    painter = QPainter(pixmap)
    painter.setPen(QColor('#444444'))
    font = QFont('Segoe UI', size // 4)
    painter.setFont(font)
    painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, '♪')
    painter.end()
    return pixmap
