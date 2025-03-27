"""
Styles.py - Contains all styles for the AnyColor application
"""

# Basic UI colors
DARK_BG = "rgb(35, 35, 35)"
DARKER_BG = "rgb(25, 25, 25)"
LIGHT_BG = "rgb(45, 45, 45)"
TEXT_COLOR = "white"
BORDER_COLOR = "#555"
EXIT_BG = "#300000"
EXIT_BG_HOVER = "#400000"

# Widget styles
LIST_WIDGET_STYLE = f"""
    QListWidget {{ 
        background-color: {DARK_BG}; 
        color: {TEXT_COLOR}; 
    }}
"""

DIRECTORY_LABEL_STYLE = f"""
    background-color:{DARK_BG}; 
    color: {TEXT_COLOR}; 
    padding: 5px;
"""

VIEW_DIRECTORY_BUTTON_STYLE = f"""
    QPushButton {{
        font-size: 14pt;
        background-color: {DARK_BG};
        color: {TEXT_COLOR};
        border: none;
        padding: 2px;
    }}
    QPushButton:hover {{
        background-color: {LIGHT_BG};
    }}
"""

WIDTH_VALUE_LABEL_STYLE = f"""
    QLabel {{
        color: {TEXT_COLOR};
        background-color: {DARK_BG};
        padding: 2px;
        border-radius: 2px;
    }}
"""

GRADIENT_GROUP_STYLE = f"""
    QGroupBox {{
        color: {TEXT_COLOR};
        border: 1px solid {BORDER_COLOR};
        border-radius: 3px;
        margin-top: 0.5em;
        padding-top: 0.5em;
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        padding: 0 5px;
    }}
"""

COLOR_PREVIEW_STYLE = "background-color: blue; border: 1px solid white;"

STATUS_TEXT_STYLE = f"""
    QTextEdit {{ 
        background-color: {DARK_BG}; 
        color: {TEXT_COLOR}; 
    }}
"""

CLEAR_STATUS_BUTTON_STYLE = f"""
    QPushButton {{
        font-size: 14pt;
        background-color: {DARK_BG};
        color: {TEXT_COLOR};
        border: none;
        padding: 2px;
    }}
    QPushButton:hover {{
        background-color: {LIGHT_BG};
    }}
"""

TRANSPARENCY_CHECKBOX_STYLE = f"""
    QCheckBox {{
        color: {TEXT_COLOR};
        padding: 5px;
    }}
"""

CONVERT_DIRECTORY_BUTTON_STYLE = """
    QPushButton {
        font-size: 10pt;
        padding: 2px;
        min-height: 30px;
    }
"""

EXIT_BUTTON_STYLE = f"""
    QPushButton {{
        background-color: {EXIT_BG};
        color: {TEXT_COLOR};
        font-size: 13pt;
        padding: 4px;
        min-height: 32px;
        margin-top: 5px;
        border: 2px solid white;
        border-radius: 4px
    }}
    QPushButton:hover {{
        background-color: {EXIT_BG_HOVER};
        border-color: #cccccc
    }}
"""

TAB_STYLE = """
    QTabBar::tab {
        font-size: 10pt;
        padding: 8px 16px;
    }
"""

# Additional widget styles
IMAGE_LABEL_STYLE = "background-color: black;"

# Function to generate dynamic styles

def get_color_preview_style(r, g, b):
    return f"background-color: rgb({r},{g},{b}); border: 1px solid white;" 