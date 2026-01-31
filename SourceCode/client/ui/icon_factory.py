"""Tạo và quản lý icon cho UI."""

from PyQt6.QtGui import QIcon, QPixmap, QPainter, QPainterPath, QColor, QPen, QBrush
from PyQt6.QtCore import Qt, QRectF

from client.ui.styles import BG_APP

class IconFactory:
    """Lớp tạo icon từ SVG paths"""
    
    # Dữ liệu đường dẫn SVG (từ Google Material Icons)
    PATHS = {
        "send": "M2.01 21L23 12 2.01 3 2 10l15 2-15 2z",
        "camera": "M9 2L7.17 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2h-3.17L15 2H9zm6 15c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5-2.24 5-5 5z",
        "clip": "M16.5 6v11.5c0 2.21-1.79 4-4 4s-4-1.79-4-4V5a2.5 2.5 0 0 1 5 0v10.5c0 .55-.45 1-1 1s-1-.45-1-1V6H10v9.5a2.5 2.5 0 0 0 5 0V5c0-2.21-1.79-4-4-4S7 2.79 7 5v12.5c0 3.04 2.46 5.5 5.5 5.5s5.5-2.46 5.5-5.5V6h-1.5z",
        "logout": "M17 7l-1.41 1.41L18.17 11H8v2h10.17l-2.58 2.58L17 17l5-5zM4 5h8V3H4c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h8v-2H4V5z",
        "user": "M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z",
        "email": "M20 4H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 4l-8 5-8-5V6l8 5 8-5v2z"
    }

    @staticmethod
    def create_icon(name, color="#FFFFFF", size=64):
        """
        Tạo QIcon từ SVG Path
        
        Tham số:
        - name: Tên icon (key trong PATHS)
        - color: Màu icon (hex)
        - size: Kích thước pixmap
        """
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        scale_factor = size / 24.0
        painter.scale(scale_factor, scale_factor)
        
        path = QPainterPath()
        
        painter.setBrush(QBrush(QColor(color)))
        painter.setPen(Qt.PenStyle.NoPen)
        
        if name == "send":
            polygon = QPainterPath()
            polygon.moveTo(2, 21); polygon.lineTo(23, 12); polygon.lineTo(2, 3)
            polygon.lineTo(2, 10); polygon.lineTo(17, 12); polygon.lineTo(2, 14)
            polygon.closeSubpath()
            painter.drawPath(polygon)
            
        elif name == "camera":
            painter.drawRoundedRect(2, 6, 20, 14, 2, 2)
            painter.drawEllipse(9, 10, 6, 6) 
            painter.drawEllipse(11, 12, 2, 2) 
            painter.drawRect(9, 3, 6, 3) 
            
        elif name == "clip":
            pen = QPen(QColor(color)); pen.setWidthF(2.5); pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(pen); painter.setBrush(Qt.BrushStyle.NoBrush)
            p = QPainterPath()
            p.moveTo(10, 8); p.lineTo(10, 19)
            p.arcTo(6, 15, 8, 8, 180, -180)
            p.lineTo(14, 6)
            p.arcTo(10, 2, 8, 8, 0, 180)
            p.lineTo(12, 15)
            painter.drawPath(p)
            
        elif name == "logout":
            path_door = QPainterPath()
            path_door.addRect(4, 3, 8, 18)
            inner = QPainterPath(); inner.addRect(6, 5, 4, 14)
            path_door = path_door.subtracted(inner)
            painter.drawPath(path_door)
            
            pen = QPen(QColor(color)); pen.setWidthF(2.5); pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(pen); painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawLine(14, 12, 22, 12) 
            painter.drawLine(19, 9, 22, 12)  
            painter.drawLine(19, 15, 22, 12) 
            
        elif name == "email":
            # Vẽ hình phong bì
            p = QPainterPath()
            p.addRect(2, 6, 20, 12) # Khung bì thư
            # Nắp bì thư (tam giác)
            triangle = QPainterPath()
            triangle.moveTo(2, 6)
            triangle.lineTo(12, 13)
            triangle.lineTo(22, 6)
            # Vì addRect đã fill, ta chỉ cần vẽ thêm nắp hoặc dùng Pen vẽ nét
            # Nhưng để đơn giản và đẹp dạng fill:
            # Ta dùng path svg chuẩn đã khai báo ở trên (cách clean nhất)
            svg_d = IconFactory.PATHS["email"]
            # PyQt không parse path string trực tiếp dễ dàng, nên vẽ thủ công hình học:
            # Vẽ thân
            painter.drawRoundedRect(2, 4, 20, 16, 2, 2)
            # Vẽ nắp (bằng Pen đè lên Brush)
            pen = QPen(QColor(BG_APP)); pen.setWidthF(2) # Màu nền để tạo khe hở
            painter.setPen(pen)
            painter.drawLine(2, 4, 12, 12)
            painter.drawLine(12, 12, 22, 4)

        painter.end()
        return QIcon(pixmap)