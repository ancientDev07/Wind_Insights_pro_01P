#start screen
import os
import json
from datetime import datetime
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from utils.async_db_worker import AsyncDBWorker
from utils.recent_projects_manager import RecentProjectsManager
# Assuming these exist based on your code
from views.dialogs.project_metadata_dialog import ProjectMetadataDialog 
from utils.progress_dialog import AnimatedProgressDialog

# --- ADOBE-STYLE DARK THEME ---
STYLESHEET = """
    QMainWindow { 
        background: #1E1E1E; /* Darker Adobe Background */
        font-family: 'Times New Roman', Arial;
        color: #D3D3D3;
    }
    
    /* SIDEBAR */
    QWidget#sidebar { 
        background: #252526; 
        border-right: 1px solid #333333;
    }
    QPushButton#sidebarBtn { 
        background: transparent; 
        border: none; 
        color: #999999; 
        padding: 12px 20px; 
        text-align: left; 
        font-size: 14px;
        border-radius: 4px;
        margin: 4px 8px;
    }
    QPushButton#sidebarBtn:hover { 
        background: #3A3D41; 
        color: #FFFFFF;
    }
    QPushButton#sidebarBtn:checked { 
        background: #3A3D41; 
        color: #FFFFFF;
        border-left: 2px solid #5DADE2; /* Blue Accent Line */
    }
    
    /* HEADERS */
    QLabel#appTitle { 
        color: #FFFFFF; 
        font-size: 18px; 
        font-weight: 600; 
        padding: 24px 20px;
        margin-bottom: 10px;
    }
    QLabel#greeting { 
        font-size: 28px; 
        font-weight: 300; 
        color: #FFFFFF; 
        margin-bottom: 20px; 
    }
    QLabel#sectionHeader {
        font-size: 14px; 
        font-weight: bold; 
        color: #CCCCCC; 
        margin: 20px 0 10px 0; 
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    /* SEARCH BOX */
    QLineEdit#searchBox { 
        padding: 10px 14px; 
        border: 1px solid #333333; 
        border-radius: 20px; /* Rounded pill shape like Adobe */
        font-size: 13px; 
        background: #252526;
        color: #FFFFFF;
        margin: 10px 0 20px 0;
    }
    QLineEdit#searchBox:focus {
        border: 1px solid #5DADE2;
        background: #1E1E1E;
    }

    /* CARDS */
    QWidget#projectCard { 
        background: #252526; 
        border: 1px solid #333333; 
        border-radius: 6px; 
    }
    QWidget#projectCard:hover { 
        background: #2A2D2E;
        border: 1px solid #555555;
        transform: translateY(-2px);
    }
    
    /* ADOBE STYLE TABLE */
    QTableWidget {
        background-color: transparent;
        border: none;
        gridline-color: transparent; /* Removes internal grid */
        selection-background-color: #094771; /* Adobe Blue Selection */
        selection-color: white;
        font-size: 13px;
        outline: none;
    }
    QTableWidget::item {
        padding: 8px 5px;
        border-bottom: 1px solid #333333; /* Very subtle separator */
        color: #CCCCCC;
    }
    QTableWidget::item:hover {
        background-color: #2A2D2E; /* Subtle hover row */
        color: #FFFFFF;
    }
    QTableWidget::item:selected {
        background-color: #094771;
        border-bottom: 1px solid #094771;
    }
    QHeaderView::section {
        background-color: transparent;
        color: #888888;
        padding: 5px;
        border: none;
        font-weight: bold;
        font-size: 11px;
        text-transform: uppercase;
        text-align: left;
    }

    /* CONTEXT MENU */
    QMenu {
        background-color: #252526;
        border: 1px solid #454545;
        color: #F0F0F0;
        padding: 5px;
    }
    QMenu::item {
        padding: 6px 24px;
        border-radius: 4px;
    }
    QMenu::item:selected {
        background-color: #094771;
        color: #FFFFFF;
    }
"""

class ProjectCreationThread(QThread):
    progress_update = pyqtSignal(int, str)
    finished_signal = pyqtSignal(int, list)
    error_signal = pyqtSignal(str)
    
    def __init__(self, metadata, data_file):
        super().__init__()
        self.metadata = metadata
        self.data_file = data_file
    
    def run(self):
        try:
            from controllers.database.database_manager import DatabaseManager
            self.progress_update.emit(0, "Initialising...")
            db = DatabaseManager()
            self.progress_update.emit(25, "Loading data file...")
            project_id, turbines = db.create_project_from_metadata(
                self.metadata, 
                self.data_file,
                progress_callback=lambda msg: self.progress_update.emit(50, f"{msg}")
            )
            self.progress_update.emit(75, "Finalising project...")
            db.close()
            self.progress_update.emit(100, "Success!")
            self.finished_signal.emit(project_id, turbines)
        except Exception as e:
            self.error_signal.emit(str(e))

class StartScreen(QMainWindow):
    project_selected = pyqtSignal(str)
    new_project_requested = pyqtSignal()
    project_created = pyqtSignal(int, str)
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Wind Data Insight Pro")
        self.setGeometry(100, 100, 1400, 850)
        
        self.recent_manager = RecentProjectsManager()
        self.recent_projects = []
        self._pending_metadata = None
        
        self.setStyleSheet(STYLESHEET)
        self.init_ui()
        self.load_recent_projects()
        
    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        sidebar = self.create_sidebar()
        
        self.content_stack = QStackedWidget()
        self.home_view = self.create_home_view()
        self.recent_view = self.create_recent_view()
        # self.settings_view = self.create_settings_view()
        # self.help_view = self.create_help_view()
        
        self.content_stack.addWidget(self.home_view)
        self.content_stack.addWidget(self.recent_view)
        # self.content_stack.addWidget(self.settings_view)
        # self.content_stack.addWidget(self.help_view)
        
        main_layout.addWidget(sidebar, 15)
        main_layout.addWidget(self.content_stack, 85)
        
    def create_sidebar(self):
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        title = QLabel("Wind Insight Pro")
        title.setObjectName("appTitle")
        layout.addWidget(title)
        
        menu_items = [
            ("🏠", "Home", 0),
            ("📂", "Your Files", 1),
            # ("⚙️", "Settings", 2),
            # ("❓", "Help", 3)
        ]
        
        self.menu_buttons = []
        for icon, text, index in menu_items:
            btn = QPushButton(f"  {icon}   {text}")
            btn.setObjectName("sidebarBtn")
            btn.setCheckable(True)
            btn.setChecked(index == 0)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda checked, idx=index: self.switch_view(idx))
            layout.addWidget(btn)
            self.menu_buttons.append(btn)
        
        layout.addStretch()
        return sidebar
    
    def switch_view(self, index):
        for i, btn in enumerate(self.menu_buttons):
            btn.setChecked(i == index)
        self.content_stack.setCurrentIndex(index)
        
        if index == 1:
            self.update_recent_table(self.recent_table, show_all=True)
        elif index == 0:
            self.update_recent_table(self.home_table, show_all=False)
        
    def create_home_view(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(40, 40, 40, 40)
        
        greeting = QLabel(self.get_time_based_greeting())
        greeting.setObjectName("greeting")
        layout.addWidget(greeting)
        
        self.home_search_box = QLineEdit()
        self.home_search_box.setObjectName("searchBox")
        self.home_search_box.setPlaceholderText("Search recent files...")
        self.home_search_box.textChanged.connect(lambda t: self._filter_table(self.home_table, t))
        layout.addWidget(self.home_search_box)
        
        new_header = QLabel("Start New")
        new_header.setObjectName("sectionHeader")
        layout.addWidget(new_header)
        
        layout.addLayout(self.create_new_projects_section())
        
        recent_header = QLabel("Recent")
        recent_header.setObjectName("sectionHeader")
        layout.addWidget(recent_header)
        
        self.home_table = self.create_projects_table()
        layout.addWidget(self.home_table)
        
        layout.addStretch()
        return widget
    
    def create_recent_view(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(40, 40, 40, 40)
        
        header = QLabel("Your Files")
        header.setObjectName("greeting")
        layout.addWidget(header)
        
        self.recent_search_box = QLineEdit()
        self.recent_search_box.setObjectName("searchBox")
        self.recent_search_box.setPlaceholderText("Filter files...")
        self.recent_search_box.textChanged.connect(lambda t: self._filter_table(self.recent_table, t))
        layout.addWidget(self.recent_search_box)
        
        self.recent_table = self.create_projects_table()
        layout.addWidget(self.recent_table)
        
        return widget
    
    # ... Settings and Help views remain similar, just styled by STYLESHEET ...
    def create_settings_view(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(40, 40, 40, 40)
        header = QLabel("Settings")
        header.setObjectName("greeting")
        layout.addWidget(header)
        # (Simplified settings for brevity, add your form here)
        layout.addStretch()
        return widget

    def create_help_view(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(40, 40, 40, 40)
        header = QLabel("Help")
        header.setObjectName("greeting")
        layout.addWidget(header)
        layout.addStretch()
        return widget
    
    def create_projects_table(self):
        """Creates table with serial number"""
        table = QTableWidget()
        table.setColumnCount(5)  # Changed from 4 to 5
        table.setHorizontalHeaderLabels(["#", "Name", "Location", "Last Opened", "Size"])
        
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Serial number
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        
        table.setShowGrid(False)
        table.verticalHeader().setVisible(False)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setSelectionMode(QAbstractItemView.SingleSelection)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.setFocusPolicy(Qt.NoFocus)
        
        table.doubleClicked.connect(self.open_project_from_table)
        table.setContextMenuPolicy(Qt.CustomContextMenu)
        table.customContextMenuRequested.connect(lambda pos: self.show_table_context_menu(table, pos))
        
        return table
    
    def show_table_context_menu(self, table, pos):
        """Context menu - updated for new column structure"""
        item = table.itemAt(pos)
        if not item:
            return
        
        row = item.row()
        path_item = table.item(row, 1)  # Changed from 0 to 1 (Name column)
        if not path_item:
            return
        
        file_path = path_item.data(Qt.UserRole)
        menu = QMenu(self)
        
        open_action = QAction("Open", self)
        open_action.triggered.connect(lambda: self.open_project_direct(file_path))
        menu.addAction(open_action)
        
        loc_action = QAction("Show in Explorer", self)
        loc_action.triggered.connect(lambda: self.open_file_location(file_path))
        menu.addAction(loc_action)
        
        menu.addSeparator()
        
        is_pinned = path_item.text().startswith("📌")
        pin_text = "Unpin from list" if is_pinned else "Pin to list"
        pin_action = QAction(pin_text, self)
        pin_action.triggered.connect(lambda: self.toggle_pin_project(table, row))
        menu.addAction(pin_action)
        
        menu.addSeparator()
        
        remove_action = QAction("Remove from Recent", self)
        remove_action.triggered.connect(lambda: self.remove_recent_project(file_path))
        menu.addAction(remove_action)
        
        menu.exec_(table.mapToGlobal(pos))

    def open_file_location(self, path):
        """Open the folder containing the file"""
        folder_path = os.path.dirname(path)
        if os.path.exists(folder_path):
            QDesktopServices.openUrl(QUrl.fromLocalFile(folder_path))
        else:
            QMessageBox.warning(self, "Error", "Folder does not exist.")

    def toggle_pin_project(self, table, row):
        """Toggle pin - updated for new column structure"""
        name_item = table.item(row, 1)  # Changed from 0 to 1
        text = name_item.text()
        if text.startswith("📌 "):
            name_item.setText(text.replace("📌 ", ""))
        else:
            name_item.setText("📌 " + text)
            
    def remove_recent_project(self, path):
        """Remove project from list"""
        confirm = QMessageBox.question(
            self, "Remove Project", 
            "Remove this project from the recent list?\n(File will not be deleted)",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm == QMessageBox.Yes:
            self.recent_manager.remove_recent_project(path)  # Fixed method name
            self.load_recent_projects()

    # def update_recent_table(self, table, show_all=False):
    #     projects = self.recent_projects if show_all else self.recent_projects[:8] # Show more in adobe style
    #     table.setRowCount(len(projects))
        
    #     for row, project in enumerate(projects):
    #         name = project.get('name', 'Unknown')
    #         # Add pin indicator if saved in project data (optional)
    #         if project.get('pinned', False):
    #             name = f"📌 {name}"
                
    #         name_item = QTableWidgetItem(name)
    #         name_item.setData(Qt.UserRole, project.get('path')) # Store path safely
            
    #         # Adobe style: location is often lighter gray
    #         location_item = QTableWidgetItem(os.path.dirname(project.get('path', '')))
    #         location_item.setForeground(QColor("#888888"))
            
    #         # Time format: "2 days ago" or "Jan 01, 2024" is better, but using standard date for now
    #         modified_str = project.get('file_modified', '')
    #         if modified_str:
    #             try:
    #                 dt = datetime.fromisoformat(modified_str)
    #                 modified_str = dt.strftime('%d-%b-%Y  %H:%M') # Cleaner format
    #             except: pass
    #         modified_item = QTableWidgetItem(modified_str)
    #         modified_item.setForeground(QColor("#888888"))
            
    #         size = project.get('file_size', 0)
    #         size_str = f"{size/1024/1024:.1f} MB"
    #         size_item = QTableWidgetItem(size_str)
    #         size_item.setForeground(QColor("#888888"))
            
    #         table.setItem(row, 0, name_item)
    #         table.setItem(row, 1, location_item)
    #         table.setItem(row, 2, modified_item)
    #         table.setItem(row, 3, size_item)
            
    #         table.setRowHeight(row, 48) # Taller rows for modern look

    def update_recent_table(self, table, show_all=False):
        """Update table with serial numbers and correct size"""
        # Remove duplicates by path
        seen_paths = set()
        unique_projects = []
        for project in self.recent_projects:
            path = project.get('path')
            if path not in seen_paths:
                seen_paths.add(path)
                unique_projects.append(project)
        
        projects = unique_projects if show_all else unique_projects[:8]
        table.setRowCount(len(projects))
        
        for row, project in enumerate(projects):
            # Serial number
            serial_item = QTableWidgetItem(str(row + 1))
            serial_item.setTextAlignment(Qt.AlignCenter)
            serial_item.setForeground(QColor("#888888"))
            table.setItem(row, 0, serial_item)
            
            # Name
            name = project.get('name', 'Unknown')
            if project.get('pinned', False):
                name = f"📌 {name}"
            name_item = QTableWidgetItem(name)
            name_item.setData(Qt.UserRole, project.get('path'))
            table.setItem(row, 1, name_item)
            
            # Location (directory name only, not full path)
            full_path = project.get('path', '')
            location = os.path.basename(os.path.dirname(full_path)) or os.path.dirname(full_path)
            location_item = QTableWidgetItem(location)
            location_item.setForeground(QColor("#888888"))
            table.setItem(row, 2, location_item)
            
            # Last opened
            modified_str = project.get('file_modified', '')
            if modified_str:
                try:
                    dt = datetime.fromisoformat(modified_str)
                    modified_str = dt.strftime('%d-%b-%Y  %H:%M')
                except:
                    pass
            modified_item = QTableWidgetItem(modified_str)
            modified_item.setForeground(QColor("#888888"))
            table.setItem(row, 3, modified_item)
            
            # Size (correct calculation)
            size = project.get('file_size', 0)
            if size < 1024:
                size_str = f"{size} B"
            elif size < 1024 * 1024:
                size_str = f"{size/1024:.1f} KB"
            else:
                size_str = f"{size/1024/1024:.2f} MB"
            size_item = QTableWidgetItem(size_str)
            size_item.setForeground(QColor("#888888"))
            table.setItem(row, 4, size_item)
            
            table.setRowHeight(row, 48)

    def open_project_from_table(self, index):
        """Open project - updated for new column structure"""
        table = self.sender()
        path = table.item(index.row(), 1).data(Qt.UserRole)  # Changed from 0 to 1
        self.open_project_direct(path)

    def open_project_direct(self, path):
        if path and os.path.exists(path):
            self.project_selected.emit(path)
            self.close()
        else:
            QMessageBox.warning(self, "Error", "Project file not found.")

    def _filter_table(self, table, text):
        search_text = text.lower()
        for row in range(table.rowCount()):
            item = table.item(row, 0)
            match = search_text in item.text().lower() if item else False
            table.setRowHidden(row, not match)
            
    # ... create_new_projects_section, create_project_card, browse_project_path remain same ...
    # (Reuse existing logic for those parts to keep response concise)
    # Be sure to include the helper methods like create_new_projects_section from previous code
    
    # --- HELPER RESTORATION (To ensure copy-paste works) ---
    def create_new_projects_section(self):
        grid = QGridLayout()
        grid.setSpacing(16)
        card = self.create_project_card("📄", "Create Project")
        grid.addWidget(card, 0, 0)
        # Multi-model project card (NEW)
        multi_card = self.create_project_card("🏭", "Multi-Model Project", "multi")
        grid.addWidget(multi_card, 0, 1)
        return grid

    # def create_project_card(self, icon, title):
    #     card = QWidget()
    #     card.setObjectName("projectCard")
    #     card.setFixedSize(160, 100) # Slightly smaller, sleeker
    #     card.setCursor(Qt.PointingHandCursor)
    #     layout = QVBoxLayout(card)
    #     layout.setContentsMargins(15, 15, 15, 15)
    #     icon_label = QLabel(icon)
    #     icon_label.setObjectName("cardIcon")
    #     icon_label.setAlignment(Qt.AlignCenter)
    #     layout.addWidget(icon_label)
    #     title_label = QLabel(title)
    #     title_label.setObjectName("cardTitle")
    #     title_label.setAlignment(Qt.AlignCenter)
    #     layout.addWidget(title_label)
    #     card.mousePressEvent = lambda e: self.handle_new_project()
    #     return card
    def create_project_card(self, icon, title, project_type="single"):
        card = QWidget()
        card.setObjectName("projectCard")
        card.setFixedSize(180, 120)  # Slightly larger for two cards
        card.setCursor(Qt.PointingHandCursor)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(15, 15, 15, 15)
        
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 32px;")
        icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon_label)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("color: #FFFFFF; font-size: 13px; font-weight: bold;")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setWordWrap(True)
        layout.addWidget(title_label)
        
        # Different click handlers based on type
        if project_type == "multi":
            card.mousePressEvent = lambda e: self.handle_multi_model_project()
        else:
            card.mousePressEvent = lambda e: self.handle_new_project()
        
        return card


    def get_time_based_greeting(self):
        h = datetime.now().hour
        return "Good Morning" if 5<=h<12 else "Good Afternoon" if 12<=h<16 else "Good Evening"

    # views/start/start_screen.py (UPDATE handle_new_project method)

    def handle_new_project(self):
        dialog = ProjectMetadataDialog(self)
        if dialog.exec_() != QDialog.Accepted:
            return
        
        metadata = dialog.get_metadata()
        data_file = metadata.get("files", {}).get("data")
        if not data_file:
            return
        
        self._pending_metadata = metadata
        
        # Create progress dialog
        self.progress_dialog = AnimatedProgressDialog(
            self, 
            "Creating Project", 
            "Initializing..."
        )
        
        # Create async worker
        self.worker = AsyncDBWorker(metadata, data_file)
        
        # Connect signals
        self.worker.progress.connect(
            lambda msg: self.progress_dialog.set_progress(
                self._calculate_progress(msg), msg
            )
        )
        self.worker.success.connect(self._on_creation_success)
        self.worker.error.connect(self._on_creation_error)
        
        # Show dialog and start worker
        self.progress_dialog.show()
        self.worker.start()

    def _calculate_progress(self, message):
        """Map message to progress percentage"""
        progress_map = {
            "Initializing": 10,
            "Creating project": 20,
            "Loading data file": 40,
            "Saving turbine data": 60,
            "Saving coordinate data": 80,
            "Saving air density data": 90
        }
        for key, value in progress_map.items():
            if key.lower() in message.lower():
                return value
        return 50

    def _on_creation_success(self, project_id, turbines):
        """Handle successful creation"""
        self.progress_dialog.set_success(f"Created with {len(turbines)} turbines")
        
        # Save project file
        meta = self._pending_metadata
        try:
            import os, json
            os.makedirs("Project", exist_ok=True)
            safe = "".join(c for c in meta['name'] if c.isalnum() or c in (' ','-','_'))
            path = os.path.join("Project", f"{safe}.wdip")
            
            with open(path, 'w') as f:
                json.dump({"metadata": meta, "db_id": project_id}, f, indent=4)
            
            self.recent_manager.add_recent_project(path)
            self.load_recent_projects()
            self.project_created.emit(project_id, meta['name'])
            
        except Exception as e:
            self._on_creation_error(str(e))

    def _on_creation_error(self, error_msg):
        """Handle creation error with retry"""
        self.progress_dialog.set_error(
            error_msg,
            retry_callback=lambda: self._retry_creation()
        )

    def _retry_creation(self):
        """Retry project creation"""
        if self._pending_metadata:
            data_file = self._pending_metadata.get("files", {}).get("data")
            self.worker = AsyncDBWorker(self._pending_metadata, data_file)
            self.worker.progress.connect(
                lambda msg: self.progress_dialog.set_progress(
                    self._calculate_progress(msg), msg
                )
            )
            self.worker.success.connect(self._on_creation_success)
            self.worker.error.connect(self._on_creation_error)
            self.worker.start()


    def _on_creation_finished(self, pid, t):
        QTimer.singleShot(500, self.progress_dialog.close)
        meta = self._pending_metadata
        try:
            os.makedirs("Project", exist_ok=True)
            safe = "".join(c for c in meta['name'] if c.isalnum() or c in (' ','-','_'))
            path = os.path.join("Project", f"{safe}.wdip")
            with open(path, 'w') as f: json.dump({"metadata":meta, "db_id":pid}, f, indent=4)
            self.recent_manager.add_recent_project(path)
            self.load_recent_projects()
            self.project_created.emit(pid, meta['name'])
        except Exception as e: self._on_creation_error(str(e))
        
    def _on_creation_error(self, err):
        self.progress_dialog.close()
        QMessageBox.critical(self, "Error", str(err))
        
    def browse_project_path(self):
        path = QFileDialog.getExistingDirectory(self, "Select Directory")
        if path :
            self.project_selected.emit(path)
        # Handle path set logic

    
    def handle_multi_model_project(self):
        """Handle multi-model project creation"""
        from views.dialogs.multi_model_project_dialog import MultiModelProjectDialog
        
        dialog = MultiModelProjectDialog(self)
        if dialog.exec_() != QDialog.Accepted:
            return
        
        metadata = dialog.get_metadata()
        data_file = metadata.get("files", {}).get("data")
        if not data_file:
            return
        
        self._pending_metadata = metadata
        
        # Create progress dialog
        self.progress_dialog = AnimatedProgressDialog(
            self, 
            "Creating Multi-Model Project", 
            "Initializing..."
        )
        
        # Create async worker
        self.worker = AsyncDBWorker(metadata, data_file)
        
        # Connect signals
        self.worker.progress.connect(
            lambda msg: self.progress_dialog.set_progress(
                self._calculate_progress(msg), msg
            )
        )
        self.worker.success.connect(self._on_creation_success)
        self.worker.error.connect(self._on_creation_error)
        
        # Show dialog and start worker
        self.progress_dialog.show()
        self.worker.start()

        
    def load_recent_projects(self):
        self.recent_projects = self.recent_manager.get_recent_projects()
        if hasattr(self, 'home_table'): self.update_recent_table(self.home_table, False)
        if hasattr(self, 'recent_table'): self.update_recent_table(self.recent_table, True)