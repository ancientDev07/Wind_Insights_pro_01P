import datetime
import os
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from config.config import ConfigurationManager
from controllers.data_controller.data_manager import DataManager
from controllers.file_menu_controller import ProjectController
from views.components.data_table_components.data_table_module import DataTableModule
from views.components.home.central_widget import CentralWidget
# from views.components.home.instructions_widget import InstructionsWidget
from views.components.home.control_panel import ControlPanel
from controllers.file_handler import FileHandler
from views.dialogs.plugin_store_dialog import PluginStoreDialog
from views.dialogs.settings_dialog import SettingsDialog
from views.components.home.menu_bar_module import MenuBarModule
from utils.logger import setup_logger
    
class WWIPApp(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.current_project_id = None
        self.current_project_name = None
        
        self.config = ConfigurationManager(json_path='config/config.json', yaml_path='config/config.yaml')
        self.project_controller = ProjectController(self)
        
        self.project_controller.project_opened.connect(self.on_project_opened)
        self.project_controller.project_saved.connect(self.on_project_saved)
        self.project_controller.project_closed.connect(self.on_project_closed)
        
        self.setWindowTitle(self.config.get('app.title', 'Wind Wise Insights Pro'))
        # Set icon first
        icon_path = os.path.join(
            self.config.get('resources.app_icon.directory', 'resources/app_icon'),
            self.config.get('resources.app_icon.app_icon', 'WWIP.ico')
        )
        self.setWindowIcon(QIcon(icon_path))
        
        # THEN set taskbar icon (Windows only)
        if os.name == 'nt':
            try:
                import ctypes
                myappid = 'tce.winddatainsightpro.1.0'
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
            except:
                pass
        
        self.data_manager = DataManager()
        self.data_table_module = DataTableModule()
        self.file_handler = FileHandler()  # Minimal DB-only version

        # Add at the end of __init__
        import sys
        if '--project' in sys.argv:
            idx = sys.argv.index('--project')
            if idx + 1 < len(sys.argv):
                project_path = sys.argv[idx + 1]
                QTimer.singleShot(100, lambda: self.project_controller._load_project_from_file(project_path))
                
        self.setup_ui()
        setup_logger(self.config.get_logging_config())
    
    def setup_ui(self):
        # Window properties
        self.setGeometry(100, 100, 1800, 1000)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2C3E50;
            }
            QLabel {
                color: #ECF0F1;
                font-size: 14px;
            }
            QWidget {
                background-color: #2C3E50;
                color: #ECF0F1;
            }
        """)

        # Central widget and main layout
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        
        self.central_widget = CentralWidget(
            parent=self, 
            data_manager=self.data_manager, 
            data_table_module=self.data_table_module,
            db_manager=self.file_handler.db_manager,  # Change this
            project_id_getter=lambda: self.current_project_id  # Add this
        )

        main_layout.addWidget(self.central_widget)

        # Set the central widget of the main window
        self.setCentralWidget(central_widget)

        # Create header layout for menubar and profile
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(0)

        # Create the advanced menubar
        self.menu_bar_module = MenuBarModule(self)
        self.setMenuBar(self.menu_bar_module)
        
        self.statusBar().showMessage('Welcome to Wind Data Insight Pro', 5000)

        # Create the control panel as a dock widget
        self.control_panel = ControlPanel(self, self.file_handler)
        self.control_panel_dock = QDockWidget("Control Panel", self)
        self.control_panel_dock.setObjectName("ControlPanelDock")
        self.control_panel_dock.setWidget(self.control_panel)
        self.control_panel_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.addDockWidget(Qt.RightDockWidgetArea, self.control_panel_dock)
        self.control_panel_dock.show()

    def open_settings(self) -> None:
        """Open the settings dialog"""
        settings_dialog = SettingsDialog(self)
        settings_dialog.exec_()

    def on_project_opened(self, project_name):
        """Handle project opened signal."""
        self.setWindowTitle(f"Wind Data Insight Pro - {project_name}")
        self.update_ui_for_project_state(True)

    def on_project_saved(self, save_path):
        """Handle project saved signal."""
        pass

    def on_project_closed(self):
        """Handle project closed signal."""
        self.setWindowTitle("Wind Data Insight Pro")
        self.update_ui_for_project_state(False)
    
    def update_ui_for_project_state(self, has_project):
        """Update UI elements based on project state."""
        if hasattr(self, 'save_action'):
            self.save_action.setEnabled(has_project)
        if hasattr(self, 'save_as_action'):
            self.save_as_action.setEnabled(has_project)
        if hasattr(self, 'close_project_action'):
            self.close_project_action.setEnabled(has_project)

    def open_plugin_store(self):
        plugin_store = PluginStoreDialog(self)
        plugin_store.exec_()

    def toggle_instructions_widget(self):
        if self.instructions_widget.isHidden():
            self.instructions_widget.show()
        else:
            self.instructions_widget.hide()

    def toggle_control_panel(self):
        if self.control_panel_dock.isHidden():
            self.control_panel_dock.hide()
        else:
            self.control_panel_dock.hide()
    
    def check_license_once(self):
        """One-time license activation check"""
        from pathlib import Path
        setup_file = Path(os.getenv('APPDATA')) / 'Wind Data Insight Pro' / 'setup_complete'
        
        if setup_file.exists():
            return True
        
        from views.dialogs.license_activation_dialog import LicenseActivationDialog
        dialog = LicenseActivationDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            setup_file.parent.mkdir(parents=True, exist_ok=True)
            setup_file.touch()
            return True
        
        QApplication.quit()
        return False

    def closeEvent(self, event):
        """Handle application close event with proper cleanup and project check."""
        try:
            # Check for unsaved project changes first
            if hasattr(self, 'project_controller'):
                if not self.project_controller._check_unsaved_changes():
                    event.ignore()
                    return
            
            # Save window state
            settings = QSettings("WindDataInsightPro", "MainWindow")
            settings.setValue("geometry", self.saveGeometry())
            settings.setValue("windowState", self.saveState())
            
            # Clean up file handler resources
            if hasattr(self, 'file_handler'):
                self.file_handler.cleanup()
                
            # Clean up matplotlib resources
            import matplotlib.pyplot as plt
            plt.close('all')
            
            # Clean up any thread pools
            if hasattr(self, 'thread_pool'):
                self.thread_pool.clear()
                
            # Force garbage collection
            import gc
            gc.collect()
            
            event.accept()
            
        except Exception as e:
            print(f"Error during cleanup: {e}")
            event.accept()

    def on_project_created_from_start(self, project_id, project_name):
        """Handle project created from start screen"""
        try:
            self.current_project_id = project_id
            self.current_project_name = project_name
            
            self.show()
            self.setWindowTitle(f"Wind Data Insight Pro - {project_name}")
            
            # Set project_id in file_handler
            if hasattr(self, 'file_handler'):
                self.file_handler.set_project_id(project_id)
            
            # FIX: Set project_id in control_panel
            if hasattr(self, 'control_panel'):
                self.control_panel.project_id = project_id
                print(f"DEBUG: Set control_panel.project_id = {project_id}")  # ADD THIS
            else:
                print("DEBUG: control_panel doesn't exist!")  # ADD THIS
            
            self.statusBar().showMessage(f"✅ Project loaded", 5000)
            
            if hasattr(self, 'start_screen'):
                self.start_screen.close()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load project:\n{str(e)}")

    def show_start_screen(self):
        """Show start screen with signal connection"""
        from views.start.start_screen import StartScreen
        
        self.start_screen = StartScreen()
        
        # Connect signals
        self.start_screen.project_created.connect(self.on_project_created_from_start)
        self.start_screen.project_selected.connect(self.on_project_selected_from_start)
        
        self.start_screen.show()

    def on_project_selected_from_start(self, project_path):
        """Handle opening existing project from recent list"""
        try:
            with open(project_path, 'r') as f:
                import json
                project_data = json.load(f)
            
            project_id = project_data.get("db_id")
            project_name = project_data.get("metadata", {}).get("name", "Unknown")
            
            if project_id:
                self.on_project_created_from_start(project_id, project_name)
            else:
                QMessageBox.warning(self, "Error", "Invalid project file")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open project:\n{str(e)}")

    
    # OPTIONAL: Handle project creation from dialog (if using this method)
    def handle_project_created_from_start_screen(self, metadata):
        """Alternative method - Handle project creation from start screen"""
        try:
            data_file = metadata.get("files", {}).get("data")
            if not data_file:
                QMessageBox.warning(self, "Error", "No data file selected!")
                return
            
            progress = QProgressDialog("Creating project...", None, 0, 100, self)
            progress.setWindowModality(Qt.WindowModal)
            progress.setValue(10)
            QApplication.processEvents()
            
            # Process file and create project in DB
            from controllers.database.database_manager import DatabaseManager
            db_manager = DatabaseManager()
            
            progress.setValue(30)
            progress.setLabelText("Processing data file...")
            QApplication.processEvents()
            
            project_id, turbines = db_manager.create_project_from_metadata(metadata, data_file)
            
            progress.setValue(70)
            progress.setLabelText("Saving project...")
            QApplication.processEvents()
            
            # Create .wdip file
            import json
            project_dir = os.path.join(os.getcwd(), "Project")
            os.makedirs(project_dir, exist_ok=True)
            
            safe_name = "".join(c for c in metadata['name'] if c.isalnum() or c in (' ', '-', '_')).rstrip()
            file_path = os.path.join(project_dir, f"{safe_name}.wdip")
            
            counter = 1
            original_path = file_path
            while os.path.exists(file_path):
                base_name = os.path.splitext(original_path)[0]
                file_path = f"{base_name}_{counter}.wdip"
                counter += 1
            
            project_data = {
                "metadata": metadata,
                "db_id": project_id,
                "created_date": datetime.now().isoformat()
            }
            
            with open(file_path, 'w') as f:
                json.dump(project_data, f, indent=4, default=str)
            
            progress.setValue(90)
            QApplication.processEvents()
            
            progress.setValue(100)
            progress.close()
            
            # Load project to UI
            self.on_project_created_from_start(project_id, metadata['name'])
            
            self.statusBar().showMessage(f"✅ Project '{metadata['name']}' created with {len(turbines)} turbines", 5000)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create project: {str(e)}")