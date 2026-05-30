from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import os
import json
from datetime import datetime

class RecentProjectsDialog(QDialog):
    def __init__(self, project_controller, parent=None):
        super().__init__(parent)
        self.project_controller = project_controller
        self.selected_project = None
        self.setup_ui()
        self.load_recent_projects()

    def setup_ui(self):
        self.setWindowTitle("Wind Data Insight Pro - Start")
        self.setFixedSize(1000, 650)
        self.setWindowFlags(Qt.Dialog | Qt.WindowCloseButtonHint)
        
        # Professional dark theme
        self.setStyleSheet("""
            QDialog {
                background-color: #2C3E50;
                color: #ECF0F1;
            }
            QWidget#sidebar {
                background-color: #34495E;
                border-right: 2px solid #3498DB;
            }
            QLabel#app_title {
                color: #ECF0F1;
                font-size: 22px;
                font-weight: bold;
                padding: 25px 20px 5px 20px;
            }
            QLabel#app_subtitle {
                color: #BDC3C7;
                font-size: 13px;
                padding: 0px 20px 25px 20px;
            }
            QLabel#section_header {
                color: #3498DB;
                font-size: 12px;
                font-weight: bold;
                padding: 20px 20px 10px 20px;
                text-transform: uppercase;
            }
            QPushButton#sidebar_btn {
                background-color: transparent;
                color: #ECF0F1;
                border: none;
                padding: 15px 20px;
                text-align: left;
                font-size: 14px;
                border-radius: 5px;
                margin: 2px 10px;
            }
            QPushButton#sidebar_btn:hover {
                background-color: #3498DB;
                color: white;
            }
            QPushButton#primary_btn {
                background-color: #3498DB;
                color: white;
                border: none;
                padding: 12px 25px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
                min-width: 120px;
            }
            QPushButton#primary_btn:hover {
                background-color: #2980B9;
            }
            QPushButton#primary_btn:disabled {
                background-color: #7F8C8D;
                color: #BDC3C7;
            }
            QPushButton#secondary_btn {
                background-color: #95A5A6;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: 500;
                font-size: 13px;
                min-width: 80px;
            }
            QPushButton#secondary_btn:hover {
                background-color: #7F8C8D;
            }
            QWidget#main_content {
                background-color: #2C3E50;
                border: none;
            }
            QLabel#content_title {
                font-size: 20px;
                font-weight: bold;
                color: #ECF0F1;
                padding: 25px 25px 15px 25px;
            }
            QTableWidget {
                background-color: #34495E;
                border: 1px solid #3498DB;
                border-radius: 8px;
                gridline-color: #2C3E50;
                selection-background-color: #3498DB;
                selection-color: white;
                outline: none;
                color: #ECF0F1;
                font-size: 13px;
            }
            QTableWidget::item {
                padding: 15px 10px;
                border-bottom: 1px solid #2C3E50;
            }
            QTableWidget::item:hover {
                background-color: #2C3E50;
            }
            QTableWidget::item:selected {
                background-color: #3498DB;
                color: white;
            }
            QHeaderView::section {
                background-color: #2C3E50;
                color: #ECF0F1;
                padding: 15px 10px;
                border: none;
                border-bottom: 2px solid #3498DB;
                font-weight: bold;
                font-size: 13px;
            }
            QLineEdit {
                background-color: #34495E;
                border: 2px solid #3498DB;
                border-radius: 6px;
                padding: 10px;
                color: #ECF0F1;
                font-size: 13px;
            }
            QLineEdit:focus {
                border-color: #2980B9;
            }
        """)
        
        # Main layout
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Create sidebar and main content
        self.create_sidebar()
        self.create_main_content()
        
        main_layout.addWidget(self.sidebar, 35)
        main_layout.addWidget(self.main_content, 65)

    def create_sidebar(self):
        self.sidebar = QWidget()
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setFixedWidth(350)
        
        layout = QVBoxLayout(self.sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # App branding
        title = QLabel("Wind Data Insight Pro")
        title.setObjectName("app_title")
        layout.addWidget(title)
        
        subtitle = QLabel("Professional Wind Analysis Platform")
        subtitle.setObjectName("app_subtitle")
        layout.addWidget(subtitle)
        
        # Quick actions section
        actions_header = QLabel("Quick Actions")
        actions_header.setObjectName("section_header")
        layout.addWidget(actions_header)
        
        new_btn = QPushButton("🆕 Create New Project")
        new_btn.setObjectName("sidebar_btn")
        new_btn.clicked.connect(self.new_project)
        layout.addWidget(new_btn)
        
        open_btn = QPushButton("📂 Open Existing Project")
        open_btn.setObjectName("sidebar_btn")
        open_btn.clicked.connect(self.browse_project)
        layout.addWidget(open_btn)
        
        # Recent projects section
        recent_header = QLabel("Recent Projects")
        recent_header.setObjectName("section_header")
        layout.addWidget(recent_header)
        
        # Recent project controls
        controls_layout = QHBoxLayout()
        controls_layout.setContentsMargins(20, 5, 20, 15)
        
        refresh_btn = QPushButton("Refresh")
        refresh_btn.setObjectName("secondary_btn")
        refresh_btn.clicked.connect(self.load_recent_projects)
        controls_layout.addWidget(refresh_btn)
        
        clear_btn = QPushButton("Clear All")
        clear_btn.setObjectName("secondary_btn")
        clear_btn.clicked.connect(self.clear_recent_projects)
        controls_layout.addWidget(clear_btn)
        
        controls_layout.addStretch()
        layout.addLayout(controls_layout)
        
        layout.addStretch()
        
        # Version info
        version = QLabel("Version 2.1.0")
        version.setObjectName("app_subtitle")
        version.setAlignment(Qt.AlignCenter)
        layout.addWidget(version)

    def create_main_content(self):
        self.main_content = QWidget()
        self.main_content.setObjectName("main_content")
        
        layout = QVBoxLayout(self.main_content)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header with title and search
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(25, 25, 25, 15)
        
        title = QLabel("Recent Projects")
        title.setObjectName("content_title")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        search_box = QLineEdit()
        search_box.setPlaceholderText("Search projects...")
        search_box.setFixedWidth(200)
        search_box.textChanged.connect(self.filter_projects)
        header_layout.addWidget(search_box)
        
        layout.addLayout(header_layout)
        
        # Projects table
        self.create_projects_table()
        table_container = QWidget()
        table_layout = QVBoxLayout(table_container)
        table_layout.setContentsMargins(25, 0, 25, 0)
        table_layout.addWidget(self.projects_table)
        layout.addWidget(table_container)
        
        # Bottom buttons
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(25, 20, 25, 25)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("secondary_btn")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        button_layout.addStretch()
        
        self.open_btn = QPushButton("Open Selected Project")
        self.open_btn.setObjectName("primary_btn")
        self.open_btn.setEnabled(False)
        self.open_btn.clicked.connect(self.open_project)
        button_layout.addWidget(self.open_btn)
        
        layout.addLayout(button_layout)
    
    def create_projects_table(self):
        self.projects_table = QTableWidget()
        self.projects_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.projects_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.projects_table.setAlternatingRowColors(True)
        self.projects_table.setSortingEnabled(True)
        self.projects_table.verticalHeader().setVisible(False)
        self.projects_table.setShowGrid(True)
        self.projects_table.setContextMenuPolicy(Qt.CustomContextMenu)  # Add this
        
        # Table columns with serial number
        columns = ["#", "Project Name", "Location", "Last Modified", "Size", "Status"]
        self.projects_table.setColumnCount(len(columns))
        self.projects_table.setHorizontalHeaderLabels(columns)
        
        # Set column widths
        header = self.projects_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        
        self.projects_table.setColumnWidth(0, 50)
        
        # Connect signals
        self.projects_table.itemSelectionChanged.connect(self.on_project_selected)
        self.projects_table.itemDoubleClicked.connect(self.open_project)
        self.projects_table.customContextMenuRequested.connect(self.show_context_menu)  # Add this
    
    def show_context_menu(self, position):
        item = self.projects_table.itemAt(position)
        if not item or item.row() < 0:
            return
        
        name_item = self.projects_table.item(item.row(), 1)
        if not name_item or not name_item.data(Qt.UserRole):
            return
        
        project_path = name_item.data(Qt.UserRole)
        
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #34495E;
                color: #ECF0F1;
                border: 1px solid #3498DB;
                border-radius: 4px;
            }
            QMenu::item {
                padding: 8px 20px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #3498DB;
            }
        """)
        
        open_action = menu.addAction(" Open Project")
        pin_action = menu.addAction(" Pin Project")
        menu.addSeparator()
        remove_action = menu.addAction("Remove from List")
        
        action = menu.exec_(self.projects_table.mapToGlobal(position))
        
        if action == open_action:
            try:
                self.project_controller._load_project_from_file(project_path)
                self.accept()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to open project: {str(e)}")
        elif action == pin_action:
            self.pin_project(project_path)
        elif action == remove_action:
            self.remove_project(project_path)

    def pin_project(self, project_path):
        """Pin/unpin project (move to top of list)"""
        recent_projects = self.project_controller.get_recent_projects()
        if project_path in recent_projects:
            recent_projects.remove(project_path)
            recent_projects.insert(0, project_path)  # Move to top
            self.project_controller.settings.setValue("recent_projects", recent_projects)
            self.project_controller.settings.sync()
            self.load_recent_projects()
            QMessageBox.information(self, "Project Pinned", "Project moved to top of the list.")

    def remove_project(self, project_path):
        """Remove project from recent list"""
        reply = QMessageBox.question(
            self,
            "Remove Project",
            f"Remove this project from recent list?\n\n{os.path.basename(project_path)}\n\nThe project file will not be deleted.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.project_controller._remove_from_recent_projects(project_path)
            self.load_recent_projects()

    def load_recent_projects(self):
        """Load recent projects into table with proper data"""
        self.projects_table.setRowCount(0)
        recent_projects = self.project_controller.get_recent_projects()
        
        if not recent_projects:
            self.projects_table.setRowCount(1)
            empty_item = QTableWidgetItem("No recent projects found")
            empty_item.setTextAlignment(Qt.AlignCenter)
            empty_item.setFlags(Qt.ItemIsEnabled)
            self.projects_table.setItem(0, 1, empty_item)
            return
        
        self.projects_table.setRowCount(len(recent_projects))
        
        for row, project_path in enumerate(recent_projects):
            try:
                with open(project_path, 'r', encoding='utf-8') as f:
                    project_data = json.load(f)
                
                metadata = project_data.get("metadata", {})
                
                # Serial number
                serial_item = QTableWidgetItem(str(row + 1))
                serial_item.setTextAlignment(Qt.AlignCenter)
                self.projects_table.setItem(row, 0, serial_item)
                
                # Project name - ensure consistency
                name = metadata.get("name", os.path.splitext(os.path.basename(project_path))[0])
                name_item = QTableWidgetItem(name)
                name_item.setData(Qt.UserRole, project_path)
                name_item.setToolTip(f"Path: {project_path}")
                self.projects_table.setItem(row, 1, name_item)
                
                # Location
                location = metadata.get("location", "Not specified")
                location_item = QTableWidgetItem(location)
                self.projects_table.setItem(row, 2, location_item)
                
                # Last modified
                last_modified = metadata.get("last_modified", "")
                modified_str = self._format_date(last_modified)
                modified_item = QTableWidgetItem(modified_str)
                self.projects_table.setItem(row, 3, modified_item)
                
                # File size
                size_str = self._get_file_size(project_path)
                size_item = QTableWidgetItem(size_str)
                self.projects_table.setItem(row, 4, size_item)
                
                # Status
                status_item = QTableWidgetItem("✅ Ready")
                status_item.setForeground(QColor("#27AE60"))
                self.projects_table.setItem(row, 5, status_item)
                
            except Exception as e:
                self._create_error_row(row, project_path, str(e))

    def _format_date(self, date_string):
        """Format ISO date string for display"""
        if not date_string:
            return "Unknown"
        
        try:
            dt = datetime.fromisoformat(date_string.replace('Z', '+00:00'))
            return dt.strftime("%m/%d/%Y %I:%M %p")
        except:
            return "Unknown"

    def _get_file_size(self, file_path):
        """Get formatted file size"""
        try:
            size = os.path.getsize(file_path)
            return self._format_file_size(size)
        except:
            return "Unknown"

    def _format_file_size(self, size_bytes):
        """Format file size in human readable format"""
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB"]
        import math
        i = int(math.floor(math.log(size_bytes, 1024)))
        p = math.pow(1024, i)
        s = round(size_bytes / p, 2)
        return f"{s} {size_names[i]}"
    
    def _create_error_row(self, row, project_path, error):
        """Create table row for corrupted project"""
        serial_item = QTableWidgetItem(str(row + 1))
        serial_item.setTextAlignment(Qt.AlignCenter)
        self.projects_table.setItem(row, 0, serial_item)
        
        error_item = QTableWidgetItem(f"⚠️ {os.path.basename(project_path)}")
        error_item.setData(Qt.UserRole, project_path)
        error_item.setToolTip(f"Error: {error}")
        error_item.setForeground(QColor("#E74C3C"))
        self.projects_table.setItem(row, 1, error_item)
        
        # Error in other columns (2-5 instead of 2-4)
        for col in range(2, 6):
            error_col_item = QTableWidgetItem("Error")
            error_col_item.setForeground(QColor("#E74C3C"))
            self.projects_table.setItem(row, col, error_col_item)


    def on_project_selected(self):
        """Handle project selection"""
        current_row = self.projects_table.currentRow()
        if current_row >= 0:
            name_item = self.projects_table.item(current_row, 1)
            if name_item and name_item.data(Qt.UserRole):
                self.selected_project = name_item.data(Qt.UserRole)
                self.open_btn.setEnabled(True)
                return
        
        self.selected_project = None
        self.open_btn.setEnabled(False)

    def filter_projects(self, text):
        """Filter projects based on search text"""
        for row in range(self.projects_table.rowCount()):
            name_item = self.projects_table.item(row, 1)
            location_item = self.projects_table.item(row, 2)
            
            if name_item and location_item:
                match = (text.lower() in name_item.text().lower() or 
                        text.lower() in location_item.text().lower())
                self.projects_table.setRowHidden(row, not match)

    def clear_recent_projects(self):
        """Clear all recent projects with confirmation"""
        reply = QMessageBox.question(
            self, 
            "Clear Recent Projects",
            "Are you sure you want to clear all recent projects?\n\nThis will not delete the project files.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.project_controller.settings.setValue("recent_projects", [])
            self.project_controller.settings.sync()
            self.load_recent_projects()

    def open_project(self):
        """Open selected project"""
        if self.selected_project:
            self.accept()


    def new_project(self):
        from views.dialogs.project_metadata_dialog import ProjectMetadataDialog
        dialog = ProjectMetadataDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            metadata = dialog.get_metadata()
            
            if hasattr(self.project_controller, 'create_new_project_with_metadata'):
                if self.project_controller.create_new_project_with_metadata(metadata):
                    self.accept()
                else:
                    QMessageBox.warning(
                        self, 
                        "Project Creation Failed", 
                        "Failed to create the new project. Please try again."
                    )
            else:
                QMessageBox.warning(
                    self, 
                    "Feature Not Available", 
                    "Project creation feature is not implemented yet."
                )

    def browse_project(self):
        self.accept()
        self.project_controller.open_project()
    
    def reject(self):
        super().reject()