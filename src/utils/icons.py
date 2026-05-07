from PyQt6.QtGui import QPixmap, QColor, QPainter, QPolygonF, QBrush, QIcon, QPen, QFont
from PyQt6.QtCore import Qt, QPointF, QRectF


def _canvas(size: int) -> tuple[QPixmap, QPainter]:
    px = QPixmap(size, size)
    px.fill(Qt.GlobalColor.transparent)
    p = QPainter(px)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setPen(Qt.PenStyle.NoPen)
    return px, p


def play_icon(size: int, color: str) -> QIcon:
    px, p = _canvas(size)
    p.setBrush(QBrush(QColor(color)))
    m = size * 0.24
    points = QPolygonF([
        QPointF(m,          m * 0.65),
        QPointF(size - m * 0.7, size / 2),
        QPointF(m,          size - m * 0.65),
    ])
    p.drawPolygon(points)
    p.end()
    return QIcon(px)


def pause_icon(size: int, color: str) -> QIcon:
    px, p = _canvas(size)
    p.setBrush(QBrush(QColor(color)))
    bw  = size * 0.20
    bh  = size * 0.52
    gap = size * 0.16
    y   = (size - bh) / 2
    x1  = (size - bw * 2 - gap) / 2
    p.drawRoundedRect(QRectF(x1,            y, bw, bh), 2, 2)
    p.drawRoundedRect(QRectF(x1 + bw + gap, y, bw, bh), 2, 2)
    p.end()
    return QIcon(px)


def prev_icon(size: int, color: str) -> QIcon:
    px, p = _canvas(size)
    p.setBrush(QBrush(QColor(color)))
    bw  = size * 0.13
    th  = size * 0.52
    y   = (size - th) / 2
    xb  = size * 0.17

    p.drawRoundedRect(QRectF(xb, y, bw, th), 2, 2)

    tx  = xb + bw + size * 0.05
    tw  = size - tx - size * 0.17
    p.drawPolygon(QPolygonF([
        QPointF(tx + tw, y),
        QPointF(tx,      size / 2),
        QPointF(tx + tw, y + th),
    ]))
    p.end()
    return QIcon(px)


def next_icon(size: int, color: str) -> QIcon:
    px, p = _canvas(size)
    p.setBrush(QBrush(QColor(color)))
    bw  = size * 0.13
    th  = size * 0.52
    y   = (size - th) / 2
    xb  = size - size * 0.17 - bw

    tx  = size * 0.17
    tw  = xb - tx - size * 0.05
    p.drawPolygon(QPolygonF([
        QPointF(tx,       y),
        QPointF(tx + tw,  size / 2),
        QPointF(tx,       y + th),
    ]))

    p.drawRoundedRect(QRectF(xb, y, bw, th), 2, 2)
    p.end()
    return QIcon(px)


def shuffle_icon(size: int, color: str) -> QIcon:
    """Icono de shuffle: dos flechas cruzadas (arriba izq→der, abajo der→izq)."""
    px, p = _canvas(size)
    c = QColor(color)
    pen = QPen(c)
    pen.setWidthF(size * 0.12)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)

    # Flecha superior: izquierda → derecha (de x1,y_top a x2,y_top)
    m = size * 0.12
    y_top = size * 0.30
    y_bot = size * 0.70
    x_left = m
    x_right = size - m

    # Línea superior
    p.drawLine(QPointF(x_left, y_top), QPointF(x_right - size * 0.14, y_top))
    # Punta de flecha superior (→)
    arr = size * 0.16
    p.setBrush(QBrush(c))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawPolygon(QPolygonF([
        QPointF(x_right, y_top),
        QPointF(x_right - arr, y_top - arr * 0.6),
        QPointF(x_right - arr, y_top + arr * 0.6),
    ]))

    # Línea inferior (der→izq)
    pen2 = QPen(c)
    pen2.setWidthF(size * 0.12)
    pen2.setCapStyle(Qt.PenCapStyle.RoundCap)
    p.setPen(pen2)
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawLine(QPointF(x_right, y_bot), QPointF(x_left + size * 0.14, y_bot))
    # Punta de flecha inferior (←)
    p.setBrush(QBrush(c))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawPolygon(QPolygonF([
        QPointF(x_left, y_bot),
        QPointF(x_left + arr, y_bot - arr * 0.6),
        QPointF(x_left + arr, y_bot + arr * 0.6),
    ]))

    p.end()
    return QIcon(px)


def repeat_icon(size: int, color: str) -> QIcon:
    """Icono de repeat: rectángulo redondeado con flecha en esquina superior derecha."""
    px, p = _canvas(size)
    c = QColor(color)
    pen = QPen(c)
    pen.setWidthF(size * 0.11)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)

    m = size * 0.14
    r = size * 0.18
    rect = QRectF(m, m + size * 0.08, size - m * 2, size - m * 2 - size * 0.08)
    p.drawRoundedRect(rect, r, r)

    # Punta de flecha en esquina superior derecha (apuntando a la derecha)
    arr = size * 0.18
    tip_x = rect.right()
    tip_y = rect.top()
    p.setBrush(QBrush(c))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawPolygon(QPolygonF([
        QPointF(tip_x, tip_y),
        QPointF(tip_x - arr, tip_y - arr * 0.55),
        QPointF(tip_x - arr, tip_y + arr * 0.55),
    ]))

    p.end()
    return QIcon(px)


def repeat_one_icon(size: int, color: str) -> QIcon:
    """Icono de repeat one: igual que repeat pero con '1' en el centro."""
    px, p = _canvas(size)
    c = QColor(color)
    pen = QPen(c)
    pen.setWidthF(size * 0.11)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)

    m = size * 0.14
    r = size * 0.18
    rect = QRectF(m, m + size * 0.08, size - m * 2, size - m * 2 - size * 0.08)
    p.drawRoundedRect(rect, r, r)

    # Punta de flecha en esquina superior derecha
    arr = size * 0.18
    tip_x = rect.right()
    tip_y = rect.top()
    p.setBrush(QBrush(c))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawPolygon(QPolygonF([
        QPointF(tip_x, tip_y),
        QPointF(tip_x - arr, tip_y - arr * 0.55),
        QPointF(tip_x - arr, tip_y + arr * 0.55),
    ]))

    # "1" en el centro
    font = QFont('Segoe UI', int(size * 0.28), QFont.Weight.Bold)
    p.setFont(font)
    p.setPen(QPen(c))
    p.drawText(QRectF(0, 0, size, size), Qt.AlignmentFlag.AlignCenter, '1')

    p.end()
    return QIcon(px)
