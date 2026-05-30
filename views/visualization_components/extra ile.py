# controllers/file_menu_controller.py
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import os
import json
import datetime
import logging
from typing import Dict, Any, Optional
from pathlib import Path
import traceback
from views.dialogs.project_metadata_dialog import ProjectMetadataDialog
from utils.recent_projects_manager import RecentProjectsManager

class ProjectController(QObject):
    # State change signals
    project_opened = pyqtSignal(str)
    project_saved = pyqtSignal(str)
    project_closed = pyqtSignal()
    project_modified = pyqtSignal()
    operation_progress = pyqtSignal(str, int)

    def _get_default_project_structure(self, metadata: Dict[str, str] = None) -> Dict[str, Any]:
        if metadata is None:
            metadata = {}
        
        now = datetime.datetime.now().isoformat()
        
        return {
            "metadata": {
                "name": metadata.get("name", "").strip() or "Untitled Project",
                "created_date": now,
                "last_modified": now,
                "version": "1.0",
                "description": metadata.get("description", "").strip(),
                "author": metadata.get("author", "").strip(),
                "capacity": metadata.get("capacity", "").strip(),
                "location": metadata.get("location", "").strip()
            },
            "data": {
                "datasets": [],
                "active_dataset": None,
                "data_sources": [],
                "preprocessing_history": []
            },
            "analysis": {
                "performed_analyses": [],
                "results": {},
                "analysis_history": [],
                "parameters": {}
            },
            "visualizations": {
                "charts": [],
                "settings": {},
                "custom_themes": [],
                "export_history": []
            },
            "settings": {
                "auto_save": True,
                "save_interval": 300,
                "default_chart_theme": "default",
                "data_precision": 4,
                "units": "metric"
            }
        }
        
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.settings = QSettings("WindDataInsightPro", "ProjectManager")
        self.recent_manager = RecentProjectsManager()
        
        self.current_project = self._get_default_project_structure()
        self.project_path = None
        self.is_modified = False
        self.PROJECT_FILE_EXTENSION = '.wdip'
        
        self._setup_logging()
        self._setup_autosave()
        self._update_window_title()
        self._load_startup_state()
    
    def _setup_logging(self) -> None:
        self.logger = logging.getLogger('ProjectController')
        self.logger.setLevel(logging.INFO)
        
        logs_dir = Path('logs')
        logs_dir.mkdir(exist_ok=True)
        
        fh = logging.FileHandler(logs_dir / 'project_controller.log')
        fh.setLevel(logging.INFO)
        
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        self.logger.addHandler(fh)

    def _load_startup_state(self) -> None:
        try:
            recent_projects = self.get_recent_projects()
            self.logger.info(f"Found {len(recent_projects)} recent projects")
        except Exception as e:
            self.logger.error(f"Error loading startup state: {str(e)}")

    def _setup_autosave(self) -> None:
        from PyQt5.QtCore import QTimer
        self.autosave_timer = QTimer(self)
        self.autosave_timer.timeout.connect(self._perform_auto_save)
        self.autosave_timer.start(300000)

    def show_status_message(self, message: str, timeout: int = 5000) -> None:
        self.main_window.statusBar().showMessage(message, timeout)

    def new_project(self) -> None:
        if not self._check_unsaved_changes():
            return
            
        metadata = self._get_project_metadata_from_dialog()
        if metadata is None:
            return
            
        self.current_project = self._get_default_project_structure(metadata)
        self.is_modified = True
        
        if self.save_project():
            self._emit_project_opened()
            self.logger.info(f"New project created: {self.current_project['metadata']['name']}")
        else:
            self._update_window_title()

    # def _load_project_from_file(self, file_path: str) -> None:
    #     progress = self._show_progress_dialog("Opening Project", "Loading project file...")
        
    #     try:
    #         progress.setValue(20)
    #         project_data = self._read_project_file(file_path)
            
    #         progress.setValue(50)
    #         self._validate_project_data(project_data)
            
    #         progress.setValue(70)
    #         self._set_current_project(project_data, file_path)
            
    #         progress.setValue(90)
    #         self._emit_project_opened()
            
    #         progress.setValue(100)
    #         self.logger.info(f"Project opened: {file_path}")
            
    #     except Exception as e:
    #         self.logger.error(f"Failed to open project: {str(e)}\n{traceback.format_exc()}")
    #         self._show_error_dialog("Failed to open project", str(e))
    #     finally:
    #         progress.close()

    def _load_project_from_file(self, file_path: str) -> None:
        progress = self._show_progress_dialog("Opening Project", "Loading project file...")
        
        try:
            progress.setValue(20)
            project_data = self._read_project_file(file_path)
            
            progress.setValue(50)
            self._validate_project_data(project_data)
            
            progress.setValue(70)
            self._set_current_project(project_data, file_path)
            
            progress.setValue(90)
            # Emit with actual project name from metadata
            project_name = project_data["metadata"]["name"]
            self.project_opened.emit(project_name)
            
            progress.setValue(100)
            self.logger.info(f"Project opened: {file_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to open project: {str(e)}\n{traceback.format_exc()}")
            self._show_error_dialog("Failed to open project", str(e))
        finally:
            progress.close()

    def _read_project_file(self, file_path: str) -> Dict[str, Any]:
        with open(file_path, 'r') as f:
            return json.load(f)

    def _set_current_project(self, project_data: Dict[str, Any], file_path: str) -> None:
        """Set current project and restore data."""
        self.current_project = project_data
        self.project_path = file_path
        self.is_modified = False
        self._update_window_title()

        # add to recent projects
        self._add_to_recent_projects(file_path)
        
        # Restore data to data_manager if available
        if (project_data.get("data", {}).get("active_dataset") and 
            hasattr(self.main_window, 'data_manager')):
            
            dataset = project_data["data"]["active_dataset"]
            if dataset.get("data"):
                import pandas as pd
                restored_data = pd.DataFrame(dataset["data"])
                
                # Load data into data_manager
                self.main_window.data_manager.load_data(restored_data)
                
                # Update UI components
                if hasattr(self.main_window, 'data_table_module'):
                    self.main_window.data_table_module.update_data_table(restored_data)
                
                if hasattr(self.main_window, 'central_widget'):
                    self.main_window.central_widget.update_data_table(restored_data)
    
    def save_project(self, save_as: bool = False) -> bool:
        """Save project with unified logic."""
        if not self.current_project:
            self._show_error_dialog("No Project Open", "Cannot save: No project is currently open.")
            return False

        # If project has a path and it's not "Save As", save directly
        if not save_as and self.project_path:
            return self._perform_save(self.project_path)
        
        # Otherwise, ask for save location
        save_path = self._get_save_path_dialog()
        if not save_path:
            return False

        return self._perform_save(save_path)

    
    # def _determine_save_path(self, save_as: bool) -> Optional[str]:
    #     if not save_as and self.project_path:
    #         return self.project_path
    #     return self._get_save_path_dialog()

    def _get_save_path_dialog(self) -> Optional[str]:
        # Use project name as default filename
        default_name = self.current_project["metadata"]["name"] if self.current_project else "Untitled Project"
        safe_name = "".join(c for c in default_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        default_path = str(Path.home() / f"{safe_name}{self.PROJECT_FILE_EXTENSION}")
        
        file_path, _ = QFileDialog.getSaveFileName(
            self.main_window,
            "Save Project",
            default_path,
            f"Wind Data Insight Pro Projects (*{self.PROJECT_FILE_EXTENSION})"
        )
        
        if file_path and not file_path.endswith(self.PROJECT_FILE_EXTENSION):
            file_path += self.PROJECT_FILE_EXTENSION
        
        return file_path
    
    # def _get_save_path_dialog(self) -> Optional[str]:
    #         #use the project name as default  file name
    #         file_path, _ = QFileDialog.getSaveFileName(
    #             self.main_window,
    #             "Save Project",
    #             str(Path.home()),
    #             f"Wind Data Insight Pro Projects (*{self.PROJECT_FILE_EXTENSION})"
    #         )
            
    #         if file_path and not file_path.endswith(self.PROJECT_FILE_EXTENSION):
    #             file_path += self.PROJECT_FILE_EXTENSION
            
    #         return file_path
    
    def _perform_save(self, save_path: str) -> bool:
        progress = self._show_progress_dialog("Saving Project", "Saving project...")
        
        try:
            progress.setValue(20)
            self._update_project_metadata()
            
            progress.setValue(60)
            if os.path.exists(save_path):
                self._create_backup(save_path)
            
            progress.setValue(80)
            self._write_project_file(save_path)
            
            progress.setValue(100)
            self._finalize_save(save_path)
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save project: {str(e)}\n{traceback.format_exc()}")
            self._show_error_dialog("Failed to save project", str(e))
            return False
        finally:
            progress.close()
    
    def _update_project_metadata(self) -> None:
        """Update project metadata and capture current data."""
        self.current_project["metadata"]["last_modified"] = datetime.datetime.now().isoformat()
        
        # Capture current data from data_manager
        if hasattr(self.main_window, 'data_manager') and self.main_window.data_manager.data is not None:
            data_dict = self.main_window.data_manager.data.to_dict('records')
            self.current_project["data"]["active_dataset"] = {
                "data": data_dict,
                "columns": list(self.main_window.data_manager.data.columns),
                "metadata": self.main_window.data_manager.metadata
            }
    
    def _write_project_file(self, save_path: str) -> None:
        with open(save_path, 'w') as f:
            json.dump(self.current_project, f, indent=4, default=str)

    def _finalize_save(self, save_path: str) -> None:
        self.project_path = save_path
        self.is_modified = False
        self._add_to_recent_projects(save_path)
        self._update_window_title()
        self.project_saved.emit(save_path)
        self.show_status_message(f"Project saved: {os.path.basename(save_path)}")

    def show_recent_projects_dialog(self):
        from views.dialogs.recent_projects_dialog import RecentProjectsDialog
        
        dialog = RecentProjectsDialog(self, self.main_window)
        result = dialog.exec_()
        
        if result == QDialog.Accepted:
            if hasattr(dialog, 'selected_project') and dialog.selected_project:
                if dialog.selected_project not in ["NEW_CREATED", "BROWSE"]:
                    self._load_project_from_file(dialog.selected_project)

    # def _update_window_title(self) -> None:
    #     if self.current_project:
    #         project_name = self.current_project["metadata"]["name"]
    #     else:
    #         project_name = "Untitled Project"
            
    #     modified_indicator = "*" if self.is_modified else ""
    #     self.main_window.setWindowTitle(
    #         f"Wind Data Insight Pro - {project_name}{modified_indicator}"
    #     )

    def _update_window_title(self) -> None:
        if self.current_project and self.current_project.get("metadata", {}).get("name"):
            project_name = self.current_project["metadata"]["name"]
        else:
            project_name = "Untitled Project"
            
        modified_indicator = "*" if self.is_modified else ""
        title = f"Wind Data Insight Pro - {project_name}{modified_indicator}"
        
        # Ensure main window title is updated
        if hasattr(self.main_window, 'setWindowTitle'):
            self.main_window.setWindowTitle(title)

    def _check_unsaved_changes(self) -> bool:
        if not self.is_modified:
            return True
            
        response = QMessageBox.question(
            self.main_window,
            "Unsaved Changes",
            "There are unsaved changes in the current project. Would you like to save them?",
            QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
            QMessageBox.Save
        )
        
        if response == QMessageBox.Save:
            return self.save_project()
        elif response == QMessageBox.Cancel:
            return False
            
        return True

    def mark_as_modified(self) -> None:
        self.is_modified = True
        self._update_window_title()
        self.project_modified.emit()

    def get_recent_projects(self):
        projects = self.recent_manager.get_recent_projects()
        return [p['path'] for p in projects]

    def _add_to_recent_projects(self, file_path: str) -> None:
        self.recent_manager.add_recent_project(file_path)

    # def _perform_auto_save(self):
    #     if (self.is_modified and self.project_path and 
    #         self.current_project["settings"].get("auto_save", True)):
            
    #         try:
    #             self.current_project["metadata"]["last_modified"] = (
    #                 datetime.datetime.now().isoformat()
    #             )
                
    #             with open(self.project_path, 'w') as f:
    #                 json.dump(self.current_project, f, indent=4, default=str)
                
    #             self.is_modified = False
    #             self._update_window_title()
    #             self.show_status_message("Project auto-saved", 2000)
                
    #         except Exception as e:
    #             self.logger.error(f"Auto-save failed: {str(e)}")

    def _perform_auto_save(self):
        if (self.is_modified and self.project_path and 
            self.current_project["settings"].get("auto_save", True)):
            
            try:
                # Update metadata and capture current data (same as regular save)
                self._update_project_metadata()
                
                with open(self.project_path, 'w') as f:
                    json.dump(self.current_project, f, indent=4, default=str)
                
                self.is_modified = False
                self._update_window_title()
                self.show_status_message("Project auto-saved", 2000)
                
            except Exception as e:
                self.logger.error(f"Auto-save failed: {str(e)}")

    
    def _show_progress_dialog(self, title: str, message: str) -> QProgressDialog:
        progress = QProgressDialog(message, "Cancel", 0, 100, self.main_window)
        progress.setWindowModality(Qt.WindowModal)
        progress.setWindowTitle(title)
        return progress
    
    def _get_project_metadata_from_dialog(self) -> Optional[Dict[str, str]]:
        dialog = ProjectMetadataDialog(self.main_window)
        if dialog.exec_() == QDialog.Accepted:
            return dialog.get_metadata()
        return None

    # def create_new_project_with_metadata(self, metadata):
    #     try:
    #         self.current_project = self._get_default_project_structure(metadata)
            
    #         project_name = metadata.get("name", "Untitled Project")
    #         project_data= {
    #             "metadata": metadata,
    #             "files": metadata.get("files", {}),  # ADD THIS LINE
    #             "data": None,
    #             "timestamp": datetime.now().isoformat()
    #         }
    #         reply = QMessageBox.question(
    #             self.main_window,
    #             "Save Project",
    #             f"Save project '{project_name}' and continue to main window?",
    #             QMessageBox.Yes | QMessageBox.No,
    #             QMessageBox.Yes
    #         )
            
    #         if reply != QMessageBox.Yes:
    #             return False
            
    #         project_dir = os.path.join(os.getcwd(), "Project")
    #         os.makedirs(project_dir, exist_ok=True)
            
    #         safe_name = "".join(c for c in project_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
    #         file_path = os.path.join(project_dir, f"{safe_name}.wdip")
            
    #         counter = 1
    #         original_path = file_path
    #         while os.path.exists(file_path):
    #             base_name = os.path.splitext(original_path)[0]
    #             file_path = f"{base_name}_{counter}.wdip"
    #             counter += 1
            
    #         with open(file_path, 'w') as f:
    #             json.dump(self.current_project, f, indent=4, default=str)
            
    #         self.project_path = file_path
    #         self.is_modified = False
            
    #         self._add_to_recent_projects(file_path)
    #         self._update_window_title()
    #         self.project_opened.emit(project_name)
            
    #         self.logger.info(f"New project created and saved: {file_path}")
    #         return True
            
    #     except Exception as e:
    #         self.logger.error(f"Error creating new project: {str(e)}")
    #         self._show_error_dialog("Failed to create new project", str(e))
    #         return False

    # Missing methods
    def _validate_file_exists(self, file_path: str) -> bool:
        return os.path.exists(file_path)

    def _validate_project_data(self, project_data: Dict[str, Any]) -> None:
        required_keys = ["metadata", "data", "analysis", "visualizations", "settings"]
        for key in required_keys:
            if key not in project_data:
                raise ValueError(f"Invalid project file: missing '{key}' section")

    def _emit_project_opened(self) -> None:
        if self.current_project:
            project_name = self.current_project["metadata"]["name"]
            self.project_opened.emit(project_name)

    def _show_error_dialog(self, title: str, message: str) -> None:
        QMessageBox.critical(
            self.main_window,
            title,
            f"{message}\n\nPlease check the log file for more details."
        )

    def _create_backup(self, file_path: str) -> None:
        try:
            import shutil
            backup_path = f"{file_path}.backup"
            shutil.copy2(file_path, backup_path)
            self.logger.info(f"Backup created: {backup_path}")
        except Exception as e:
            self.logger.warning(f"Failed to create backup: {str(e)}")

    # def open_project(self) -> None:
    #     if not self._check_unsaved_changes():
    #         return
        
    #     file_path = self._get_open_file_path()
    #     if file_path:
    #         self._load_project_from_file(file_path)

    def create_new_project_with_metadata(self, metadata):
        """Create a new project with metadata from the dialog."""
        try:
            # Create project structure
            self.current_project = self._get_default_project_structure(metadata)
            self.current_project["files"] = metadata.get("files", {})
            
            # Get save location
            default_name = metadata.get('name', 'Untitled') + self.PROJECT_FILE_EXTENSION
            save_path, _ = QFileDialog.getSaveFileName(
                self.main_window,
                "Save Project As",
                os.path.join(os.path.expanduser('~'), 'Documents', default_name),
                f"Wind Data Insight Pro Files (*{self.PROJECT_FILE_EXTENSION})"
            )
            
            if not save_path:
                return False
            
            if not save_path.endswith(self.PROJECT_FILE_EXTENSION):
                save_path += self.PROJECT_FILE_EXTENSION
            
            # Save project file
            with open(save_path, 'w') as f:
                json.dump(self.current_project, f, indent=4, default=str)
            
            # Update state
            self.project_path = save_path
            self.is_modified = False
            
            # Add to recent projects
            self._add_to_recent_projects(save_path)
            
            # Update UI
            self._update_window_title()
            
            # Load data file if provided
            data_file = metadata.get("files", {}).get("data")
            if data_file and os.path.exists(data_file) and hasattr(self.main_window, 'control_panel'):
                QTimer.singleShot(500, lambda: self.main_window.control_panel.load_project_data_file(data_file))
            
            # Emit signal
            project_name = metadata.get('name', 'Untitled')
            self.project_opened.emit(project_name)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error creating project: {str(e)}")
            self._show_error_dialog("Failed to create project", str(e))
            return False


    def open_project(self, project_path=None):
        """
        Open an existing project file.
        Loads project data and auto-loads data file through Control Panel pipeline.
        """
        try:
            # Check for unsaved changes
            if not self._check_unsaved_changes():
                return False
            
            # Get project file path
            if not project_path:
                project_path, _ = QFileDialog.getOpenFileName(
                    self.main_window,
                    "Open Project",
                    os.path.expanduser('~'),
                    "Wind Data Insight Pro Files (*.wdip)"
                )
            
            if not project_path:
                return False
            
            # Load project data
            with open(project_path, 'r') as f:
                project_data = json.load(f)
            
            # Update project state
            self.current_project_path = project_path
            self.is_modified = False
            project_name = project_data.get("metadata", {}).get("name", "Untitled")
            self.project_name = project_name
            
            # Add to recent projects
            self.recent_manager.add_recent_project(project_path)
            
            # ADDED: Auto-load data file through Control Panel pipeline
            data_file = project_data.get("files", {}).get("data")
            if data_file and os.path.exists(data_file):
                if hasattr(self.main_window, 'control_panel'):
                    self.main_window.control_panel.load_project_data_file(data_file)
            
            # Emit signal
            self.project_opened.emit(project_name)
            
            return True
            
        except Exception as e:
            QMessageBox.critical(
                self.main_window,
                "Error",
                f"Failed to open project: {str(e)}"
            )
            return False

        
    def closed_project(self) -> bool:
        try :
            if not self._check_unsaved_changes():
                return False
            
            if self.current_project:
                self.logger.info(f"Closing project: {self.project_path or 'Untitled'}")

                # cler project data
                self.current_project = self._get_default_project_structure()
                self.project_path = None
                self.is_modified = False

                # update ui
                self._update_window_title()
                self.show_status_message("Project closed")
                self.project_closed.emit()

                return True 
            return False
        
        except Exception as e:
            self.logger.error(f"Error closing project: {str(e)}")
            self._show_error_dialog("Failed to close project", str(e))
            return False
        
    def _get_open_file_path(self)-> Optional[str]:
        file_path, _ = QFileDialog.getOpenFileName(
            self.main_window,
            "Open Project",
            str(Path.home()),
            f"Wind Data Insight Pro Projects (*{self.PROJECT_FILE_EXTENSION})"
        )
        return file_path if file_path else None


    # def _handle_ad_correction(self):
    #     if self.enable_air_density_correction.isChecked():
    #         if not self.client_power_data:
    #             QMessageBox.warning(self, "Warning", "Please upload client power curve first")
    #             self.enable_air_density_correction.setChecked(False)
    #             return
            
    #         elevation, ok1 = QInputDialog.getDouble(self, "Elevation", "Enter elevation (m):", 0, 0, 5000, 1)
    #         if not ok1:
    #             self.enable_air_density_correction.setChecked(False)
    #             return
            
    #         hub_height, ok2 = QInputDialog.getDouble(self, "Hub Height", "Enter hub height (m):", 80, 0, 200, 1)
    #         if not ok2:
    #             self.enable_air_density_correction.setChecked(False)
    #             return
            
    #         try:
    #             from views.visualization_components import air_density_correction as adc
                
    #             T_hub_avg = adc.get_t_hub_average(self.filtered_df)
    #             rho_site = adc.calculate_air_density(elevation, hub_height, T_hub_avg)
    #             self.ad_corrected_data = adc.normalize_wind_speed_power(self.client_power_data, rho_site)
                
    #             self.ad_data_table.setRowCount(len(self.ad_corrected_data))
    #             for row, (ws, pwr) in enumerate(zip(self.ad_corrected_data['wind_speed_normalized'], 
    #                                                   self.ad_corrected_data['power_corrected'])):
    #                 self.ad_data_table.setItem(row, 0, QTableWidgetItem(f"{ws:.2f}"))
    #                 self.ad_data_table.setItem(row, 1, QTableWidgetItem(f"{pwr:.2f}"))
    #             self.ad_data_table.resizeColumnsToContents()
    #             self.ad_data_dock.setVisible(True)
                
    #             QMessageBox.information(self, "Success", 
    #                 f"Air Density Correction Applied\nT_hub: {T_hub_avg:.2f}°C\nρ_site: {rho_site:.3f} kg/m³")
    #         except Exception as e:
    #             QMessageBox.critical(self, "Error", f"AD correction failed: {e}")
    #             self.enable_air_density_correction.setChecked(False)
    #     else:
    #         self.ad_data_dock.setVisible(False)
        
    #     self.update_plot()

    # corrected flow of data of cordinate:
    # def _handle_ad_correction(self):
    #     if self.enable_air_density_correction.isChecked():
    #         if not self.client_power_data:
    #             QMessageBox.warning(self, "Warning", "Please upload client power curve first")
    #             self.enable_air_density_correction.setChecked(False)
    #             return
            
    #         # Get coordinate data from project
    #         if not hasattr(self.parent(), 'project_controller') or not self.parent().project_controller.current_project_path:
    #             QMessageBox.warning(self, "Warning", "No project loaded")
    #             self.enable_air_density_correction.setChecked(False)
    #             return
            
    #         try:
    #             import json
    #             with open(self.parent().project_controller.current_project_path, 'r') as f:
    #                 project_data = json.load(f)
                
    #             coord_file = project_data.get("files", {}).get("coordinate")
    #             if not coord_file:
    #                 QMessageBox.warning(self, "Warning", "Coordinate file not found in project")
    #                 self.enable_air_density_correction.setChecked(False)
    #                 return
                
    #             # Load coordinate data
    #             import pandas as pd
    #             if coord_file.endswith('.xlsx'):
    #                 coord_df = pd.read_excel(coord_file)
    #             else:
    #                 coord_df = pd.read_csv(coord_file)

    #             # Use SCADA dictionary to find columns
    #             import models.scada_utils as su
    #             hub_height_cols = su.find_matching_columns(coord_df, 'hub_height')
    #             elevation_cols = su.find_matching_columns(coord_df, 'elevation')
                
    #             # Get elevation and hub_height for current turbine
    #             turbine_id = self.turbine_name  # Assuming turbine_name is set
    #             turbine_data = coord_df[coord_df['turbine_id'] == turbine_id]
                
    #             if turbine_data.empty:
    #                 QMessageBox.warning(self, "Warning", f"Turbine {turbine_id} not found in coordinate file")
    #                 self.enable_air_density_correction.setChecked(False)
    #                 return
                
    #             elevation = float(turbine_data['elevation'].iloc[0])
    #             hub_height = float(turbine_data['hub_height'].iloc[0])
                
    #             # Calculate AD correction
    #             from views.visualization_components import air_density_correction as adc
                
    #             T_hub_avg = adc.get_t_hub_average(self.filtered_df)
    #             rho_site = adc.calculate_air_density(elevation, hub_height, T_hub_avg)
    #             self.ad_corrected_data = adc.normalize_wind_speed_power(self.client_power_data, rho_site)
                
    #             # Populate table...
    #             self.ad_data_table.setRowCount(len(self.ad_corrected_data))
    #             for row, (ws, pwr) in enumerate(zip(self.ad_corrected_data['wind_speed_normalized'], 
    #                                                   self.ad_corrected_data['power_corrected'])):
    #                 self.ad_data_table.setItem(row, 0, QTableWidgetItem(f"{ws:.2f}"))
    #                 self.ad_data_table.setItem(row, 1, QTableWidgetItem(f"{pwr:.2f}"))
    #             self.ad_data_table.resizeColumnsToContents()
    #             self.ad_data_dock.setVisible(True)
                
    #             QMessageBox.information(self, "Success", 
    #                 f"Air Density Correction Applied\nTurbine: {turbine_id}\nElevation: {elevation}m\nHub Height: {hub_height}m\nT_hub: {T_hub_avg:.2f}°C\nρ_site: {rho_site:.3f} kg/m³")
    #         except Exception as e:
    #             QMessageBox.critical(self, "Error", f"AD correction failed: {e}")
    #             self.enable_air_density_correction.setChecked(False)
    #     else:
    #         self.ad_data_dock.setVisible(False)
        
    #     self.update_plot()

    # def _handle_ad_correction(self):
        if self.enable_air_density_correction.isChecked():
            if self.client_power_data is None or self.client_power_data.empty:
                QMessageBox.warning(self, "Warning", "Please upload client power curve first")
                self.enable_air_density_correction.setChecked(False)
                return
            
            try:
                import json
                import models.scada_utils as su
                
                # Get coordinate file from project
                with open(self.parent().project_controller.current_project_path, 'r') as f:
                    project_data = json.load(f)
                
                coord_file = project_data.get("files", {}).get("coordinate")
                if not coord_file:
                    QMessageBox.warning(self, "Warning", "Coordinate file not found in project")
                    self.enable_air_density_correction.setChecked(False)
                    return
                
                # Load coordinate data
                if coord_file.endswith('.xlsx'):
                    coord_df = pd.read_excel(coord_file)
                else:
                    coord_df = pd.read_csv(coord_file)
                
                # Use SCADA dictionary to find columns
                hub_height_cols = su.find_matching_columns(coord_df, 'hub_height')
                elevation_cols = su.find_matching_columns(coord_df, 'elevation')
                
                if not hub_height_cols or not elevation_cols:
                    QMessageBox.warning(self, "Warning", "Hub Height or Elevation columns not found in coordinate file")
                    self.enable_air_density_correction.setChecked(False)
                    return
                
                # Get values for current turbine
                turbine_id = self.turbine_name
                turbine_data = coord_df[coord_df['turbine_id'] == turbine_id]
                
                if turbine_data.empty:
                    # Use first row if turbine not found
                    elevation = float(coord_df[elevation_cols[0]].iloc[0])
                    hub_height = float(coord_df[hub_height_cols[0]].iloc[0])
                else:
                    elevation = float(turbine_data[elevation_cols[0]].iloc[0])
                    hub_height = float(turbine_data[hub_height_cols[0]].iloc[0])
                
                # Calculate AD correction
                from views.visualization_components import air_density_correction as adc
                
                T_hub_avg = adc.get_t_hub_average(self.filtered_df)
                rho_site = adc.calculate_air_density(elevation, hub_height, T_hub_avg)
                self.ad_corrected_data = adc.normalize_wind_speed_power(self.client_power_data, rho_site)
                
                # Populate table
                self.ad_data_table.setRowCount(len(self.ad_corrected_data))
                for row, (ws, pwr) in enumerate(zip(self.ad_corrected_data['wind_speed_normalized'], 
                                                      self.ad_corrected_data['power_corrected'])):
                    self.ad_data_table.setItem(row, 0, QTableWidgetItem(f"{ws:.2f}"))
                    self.ad_data_table.setItem(row, 1, QTableWidgetItem(f"{pwr:.2f}"))
                self.ad_data_table.resizeColumnsToContents()
                self.ad_data_dock.setVisible(True)
                
                QMessageBox.information(self, "Success", 
                    f"Air Density Correction Applied\nTurbine: {turbine_id}\nElevation: {elevation}m\nHub Height: {hub_height}m\nT_hub: {T_hub_avg:.2f}°C\nρ_site: {rho_site:.3f} kg/m³")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"AD correction failed: {e}")
                self.enable_air_density_correction.setChecked(False)
        else:
            self.ad_data_dock.setVisible(False)
        
        self.update_plot()
