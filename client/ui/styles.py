"""Mô-đun client\ui\styles.py - mô tả ngắn bằng tiếng Việt."""

# ==================== BẢNG MÀU CHÍNH ====================
PRIMARY       = "#5865F2"   # Màu tím xanh đặc trưng
PRIMARY_HOVER = "#4752C4"
BG_APP        = "#313338"   # Nền chính tối
BG_SIDEBAR    = "#2B2D31"   # Nền sidebar tối hơn chút
BG_CARD       = "#232428"   # Nền user card
BG_INPUT      = "#383A40"   # Nền ô nhập liệu
TEXT_MAIN     = "#F2F3F5"   # Trắng sáng
TEXT_SUB      = "#949BA4"   # Xám nhạt
GREEN         = "#23A559"   # Online status
RED           = "#DA373C"   # Logout/Error
DIVIDER       = "#1E1F22"   # Đường kẻ

# Màu Bong bóng chat
ME_BUBBLE     = "#5865F2"   # Tím xanh
THEM_BUBBLE   = "#2B2D31"   # Xám đậm (cùng màu sidebar)

# --- GLOBAL STYLESHEET (Thêm Scrollbar đẹp) ---
GLOBAL_STYLE = f"""
    * {{ outline: none; border: none; }} 

    QMainWindow, QDialog, QWidget#CentralWidget {{
        background-color: {BG_APP};
    }}
    
    QLabel, QLineEdit, QPushButton, QTextEdit, QFrame {{
        font-family: 'Segoe UI', 'Roboto', sans-serif;
        font-size: 14px;
        color: {TEXT_MAIN};
    }}

    /* Input Fields */
    QLineEdit {{
        background-color: transparent;
        color: {TEXT_MAIN};
        font-size: 15px;
        padding: 5px;
    }}
    
    /* List Widget (Members) */
    QListWidget {{
        background-color: transparent;
        border: none;
        outline: none;
    }}
    QListWidget::item {{
        padding: 8px;
        border-radius: 4px;
        color: {TEXT_SUB};
    }}
    QListWidget::item:hover {{
        background-color: {BG_INPUT};
        color: {TEXT_MAIN};
    }}

    /* SCROLLBAR ĐẸP (Quan trọng) */
    QScrollBar:vertical {{
        border: none;
        background: {BG_APP};
        width: 10px;
        margin: 0px;
    }}
    QScrollBar::handle:vertical {{
        background: #1A1B1E;
        min-height: 30px;
        border-radius: 5px;
    }}
    QScrollBar::handle:vertical:hover {{ background: #404249; }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: none; }}
    
    /* Tooltip */
    QToolTip {{ 
        color: #ffffff; 
        background-color: #111214; 
        border: 1px solid {BG_INPUT}; 
        border-radius: 4px;
        padding: 5px;
    }}
"""

# Style cho nút bấm
BTN_PRIMARY = f"""
    QPushButton {{
        background-color: {PRIMARY}; 
        color: white; 
        border-radius: 5px; 
        font-weight: bold; 
        padding: 8px 16px;
    }}
    QPushButton:hover {{ background-color: {PRIMARY_HOVER}; }}
    QPushButton:pressed {{ background-color: #3C45A5; }}
"""

BTN_GHOST = f"""
    QPushButton {{
        background-color: transparent;
        color: {TEXT_SUB};
        border-radius: 4px;
        text-align: left;
        padding: 8px;
        font-weight: 600;
    }}
    QPushButton:hover {{
        background-color: {BG_INPUT};
        color: {TEXT_MAIN};
    }}
"""

BTN_PRIMARY = f"background-color: {PRIMARY}; color: white; border-radius: 3px; font-weight: bold; padding: 10px;"
BTN_GREEN   = f"background-color: {GREEN}; color: white; border-radius: 3px; font-weight: bold; padding: 10px;"