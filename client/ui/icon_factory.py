# client/ui/icon_factory.py
from PyQt6.QtGui import QPixmap, QPainter, QColor, QPen, QFont
from PyQt6.QtCore import Qt, QSize

class IconFactory:
    """
    Tạo icon bằng code (QPainter) thay vì load file ảnh.
    Giúp ứng dụng nhẹ và không bị lỗi thiếu resource.
    """
    
    @staticmethod
    def create_circle_icon(color, size=40, text=""):
        """Tạo icon hình tròn (Avatar placeholder)"""
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Vẽ hình tròn
        painter.setBrush(QColor(color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(0, 0, size, size)
        
        # Vẽ chữ (nếu có)
        if text:
            painter.setPen(QColor("white"))
            font = QFont("Segoe UI", int(size/2.5), QFont.Weight.Bold)
            painter.setFont(font)
            painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, text[:2].upper())
            
        painter.end()
        return pixmap

    @staticmethod
    def create_hashtag_icon(color="#B5BAC1", size=24):
        """Tạo icon dấu thăng (#) cho kênh chat"""
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        pen = QPen(QColor(color))
        pen.setWidth(2)
        painter.setPen(pen)
        
        # Vẽ dấu #
        m = 6 # margin
        s = size - m
        painter.drawLine(m+4, m, m+4, s) # Dọc 1
        painter.drawLine(s-4, m, s-4, s) # Dọc 2
        painter.drawLine(m, m+6, s, m+6) # Ngang 1
        painter.drawLine(m, s-6, s, s-6) # Ngang 2
        
        painter.end()
        return pixmap