"""Thông báo toast tạm thời."""

from PyQt6.QtWidgets import QLabel, QGraphicsDropShadowEffect
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QTimer, QPoint
from PyQt6.QtGui import QColor
from client.ui.styles import RED, GREEN

class ToastNotification(QLabel):
    """Thông báo Toast trượt từ trên xuống"""
    
    def __init__(self, parent, message, is_error=False):
        super().__init__(parent)
        self.setText(message)
        
        bg_color = RED if is_error else GREEN
        self.setStyleSheet(f"""
            background-color: {bg_color}; 
            color: white; 
            padding: 10px 24px; 
            border-radius: 20px; 
            font-weight: 600; 
            font-size: 13px;
            border: 1px solid rgba(255,255,255,0.2);
        """)
        
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0,0,0,80))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)
        
        self.adjustSize()
        
        if parent:
            parent_w = parent.width()
            my_w = self.width()
            # Canh giữa theo chiều ngang, tính từ mép phải của sidebar (giả định 280px)
            # Hoặc canh giữa màn hình
            sidebar_w = 280 
            self.target_x = sidebar_w + (parent_w - sidebar_w - my_w) // 2
            self.target_y = 40
            self.start_y = -self.height() - 20
            self.move(self.target_x, self.start_y)
        else:
            self.move(100, 100)

        self.show()
        self.raise_()
        
        # Animation In
        self.anim_in = QPropertyAnimation(self, b"pos")
        self.anim_in.setDuration(600)
        self.anim_in.setStartValue(QPoint(self.target_x, self.start_y))
        self.anim_in.setEndValue(QPoint(self.target_x, self.target_y))
        self.anim_in.setEasingCurve(QEasingCurve.Type.OutBack) 
        self.anim_in.start()
        
        QTimer.singleShot(2500, self.start_close)

    def start_close(self):
        # Animation Out
        self.anim_out = QPropertyAnimation(self, b"pos")
        self.anim_out.setDuration(400)
        self.anim_out.setStartValue(self.pos())
        self.anim_out.setEndValue(QPoint(self.x(), self.start_y)) 
        self.anim_out.setEasingCurve(QEasingCurve.Type.InBack)
        self.anim_out.finished.connect(self.close)
        self.anim_out.start()