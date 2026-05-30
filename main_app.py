import sys
import os

from PyQt5.QtCore import *
QCoreApplication.setAttribute(Qt.AA_ShareOpenGLContexts)

from PyQt5.QtWidgets import *
from PyQt5.QtGui import QIcon
import qdarkstyle
from WWIP_APP import WWIPApp
from config.config import ConfigurationManager
from utils.splash_generator import create_professional_splash
from utils.logger import setup_logger, logger
import traceback
import argparse
from views.start.start_screen import StartScreen


def global_exception_handler(exctype, value, tb):
    error_msg = ''.join(traceback.format_exception(exctype, value, tb))
    logger.critical(f"Uncaught exception: {error_msg}")
    sys.__excepthook__(exctype, value, tb)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--project', type=str)
    parser.add_argument('--start-screen', action='store_true')
    return parser.parse_args()

class AppLauncher:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.config = ConfigurationManager(json_path='config/config.json', yaml_path='config/config.yaml')
        log_config = self.config.get_logging_config()
        self.logger = setup_logger(log_config)
        self.logger.info("Application starting")
        sys.excepthook = global_exception_handler
        self.setup_app()
        self.splash = None
        self.main_window = None

    def setup_app(self):
        self.app.setOrganizationName("Tata Consulting Engineers")
        self.app.setOrganizationDomain("https://www.tataconsultingengineers.com/")
        self.app.setApplicationName("Wind Data Insight Pro")
        self.app.setApplicationVersion("1.0.0")
        
        if self.config.get('app.style') == 'dark':
            self.app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
            self.logger.info("Applied dark theme")
        
        icon_path = os.path.join('resources', 'app_icon', 'WWIP.ico')
        if os.path.exists(icon_path):
            self.app.setWindowIcon(QIcon(icon_path))
            self.logger.debug(f"Set application icon: {icon_path}")
        else:
            self.logger.warning(f"Icon not found at path: {icon_path}")

    def show_splash(self):
        self.logger.info("Showing splash screen")
        app_logo = os.path.join('resources', 'app_icon', 'WWIP.ico')
        brand_logo = os.path.join('resources', 'app_icon', 'brand_logo.png')
        self.splash = create_professional_splash(
            app_logo if os.path.exists(app_logo) else None,
            brand_logo if os.path.exists(brand_logo) else None
        )
        self.splash.show()
        
        if hasattr(self.splash, "animate_progress"):
            self.splash.animate_progress()
        
        QTimer.singleShot(3000, self._show_main_after_splash)

    def _show_main_after_splash(self):
        if self.splash:
            self.splash.close()
        
        from pathlib import Path
        agreement_file = Path(os.getenv('APPDATA')) / 'Wind Data Insight Pro' / 'agreement_accepted'
        
        # Check license agreement (only once)
        if not agreement_file.exists():
            from views.dialogs.license_agreement_dialog import LicenseAgreementDialog
            agreement_dialog = LicenseAgreementDialog()
            if agreement_dialog.exec_() != QDialog.Accepted:
                self.app.quit()
                return
            
            agreement_file.parent.mkdir(parents=True, exist_ok=True)
            agreement_file.touch()
        
        # Show start screen
        self.start_screen = StartScreen()
        self.start_screen.project_selected.connect(self.open_project)
        self.start_screen.project_created.connect(self.create_project_and_show_main)
        self.start_screen.show()   
    
    def run(self):
        self.logger.info("Starting application flow")
        self.show_splash()
        return self.app.exec_()
    
    def open_project(self, path):
        if hasattr(self, 'start_screen'):
            self.start_screen.close()
        self.main_window = WWIPApp()
        self.main_window.show()
        # Load the project after the window is shown
        QTimer.singleShot(100, lambda: self.main_window.project_controller._load_project_from_file(path))
  
    def show_main_window(self):
        if hasattr(self, 'start_screen'):
            self.start_screen.close()
        self.main_window = WWIPApp()
        self.main_window.show()

    def create_project_and_show_main(self, project_id, project_name):
        """Handle project created from start screen"""
        if hasattr(self, 'start_screen'):
            self.start_screen.close()
        
        self.main_window = WWIPApp()
        self.main_window.on_project_created_from_start(project_id, project_name)
        self.main_window.show()

# def main():
#     try:
#         launcher = AppLauncher()
#         return launcher.run()
#     except Exception as e:
#         if 'logger' in globals():
#             logger.critical(f"Fatal error in main: {str(e)}", exc_info=True)
#         else:
#             print(f"Fatal error before logger initialization: {str(e)}")
#             traceback.print_exc()
#         return 1

def main():
    try:
        args = parse_args()
        launcher = AppLauncher()
        
        if args.project and os.path.exists(args.project):
            # Direct project load
            launcher.main_window = WWIPApp()
            launcher.main_window.show()
            QTimer.singleShot(100, lambda: launcher.main_window.project_controller._load_project_from_file(args.project))
            return launcher.app.exec_()
        elif args.start_screen:
            # Show start screen only
            launcher.start_screen = StartScreen()
            launcher.start_screen.project_selected.connect(launcher.open_project)
            launcher.start_screen.project_created.connect(launcher.create_project_and_show_main)
            launcher.start_screen.show()
            return launcher.app.exec_()
        else:
            # Normal flow with splash
            return launcher.run()
    except Exception as e:
        logger.critical(f"Fatal error: {str(e)}", exc_info=True)
        return 1

if __name__ == '__main__':
    sys.exit(main())