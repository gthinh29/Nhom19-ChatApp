# client/ui/styles.py

# Bảng màu (Discord Dark Theme Palette)
COLORS = {
    "BACKGROUND": "#313338",       # Màu nền chính (Chat area)
    "SIDEBAR": "#2B2D31",          # Sidebar (Channel list)
    "SERVER_LIST": "#1E1F22",      # Server list (Leftmost)
    "INPUT_BG": "#383A40",         # Ô nhập liệu
    "PRIMARY": "#5865F2",          # Màu tím Discord (Blurple)
    "PRIMARY_HOVER": "#4752C4",
    "TEXT_MAIN": "#F2F3F5",        # Trắng sáng
    "TEXT_MUTED": "#B5BAC1",       # Xám nhạt
    "DANGER": "#DA373C",           # Đỏ (Error/Delete)
    "SUCCESS": "#23A559",          # Xanh lá (Online)
    "SCROLLBAR": "#1A1B1E",
    "SCROLLBAR_HANDLE": "#2B2D31",
    "MESSAGE_HOVER": "#2e3035"     # Màu nền khi di chuột vào tin nhắn
}

# Stylesheet toàn cục (QSS)
GLOBAL_STYLES = f"""
    QWidget {{
        background-color: {COLORS["BACKGROUND"]};
        color: {COLORS["TEXT_MAIN"]};
        font-family: 'gg sans', 'Segoe UI', 'Helvetica Neue', Helvetica, Arial, sans-serif;
        font-size: 14px;
    }}
    
    /* --- Input Field --- */
    QLineEdit {{
        background-color: {COLORS["INPUT_BG"]};
        border: none;
        padding: 12px;
        border-radius: 8px;
        color: {COLORS["TEXT_MAIN"]};
        font-size: 14px;
    }}
    QLineEdit:focus {{
        color: white;
    }}

    /* --- Buttons --- */
    QPushButton {{
        background-color: {COLORS["PRIMARY"]};
        color: white;
        border: none;
        padding: 10px 20px;
        border-radius: 4px;
        font-weight: bold;
        font-size: 14px;
    }}
    QPushButton:hover {{
        background-color: {COLORS["PRIMARY_HOVER"]};
    }}
    QPushButton:pressed {{
        background-color: {COLORS["SERVER_LIST"]};
    }}
    
    /* --- Scrollbar (Discord Style) --- */
    QScrollBar:vertical {{
        border: none;
        background: {COLORS["SIDEBAR"]};
        width: 14px;
        margin: 0px;
    }}
    QScrollBar::handle:vertical {{
        background: {COLORS["SERVER_LIST"]};
        min-height: 20px;
        border-radius: 7px;
        margin: 2px;
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}
    
    /* --- Labels --- */
    QLabel#Title {{
        font-size: 24px;
        font-weight: bold;
        color: {COLORS["TEXT_MAIN"]};
        margin-bottom: 20px;
    }}
    QLabel#Error {{
        color: {COLORS["DANGER"]};
        font-size: 12px;
    }}
    QLabel#SubText {{
        color: {COLORS["TEXT_MUTED"]};
        font-size: 12px;
    }}
"""