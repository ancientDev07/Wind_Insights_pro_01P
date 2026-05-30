import qdarkstyle
from PyQt5.QtWidgets import QApplication
import logging

logger = logging.getLogger(__name__)

def apply_theme(app: QApplication, theme_name: str):
    """
    Applies a theme to the entire application.
    
    Args:
        app: The QApplication instance.
        theme_name: The name of the theme ('Light', 'Dark', 'System').
    """
    logger.info(f"Attempting to apply theme: {theme_name}")
    if theme_name == "Dark":
        stylesheet = qdarkstyle.load_stylesheet_pyqt5()
    elif theme_name in ["Light", "System"]:
        # Reset to a basic light theme stylesheet. 'System' defaults to 'Light'.
        stylesheet = "" 
    else:
        logger.warning(f"Unknown theme '{theme_name}'. Defaulting to light theme.")
        stylesheet = ""
        
    app.setStyleSheet(stylesheet)