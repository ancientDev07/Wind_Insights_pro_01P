from PyQt5.QtWidgets import QMenuBar, QMenu, QAction
from PyQt5.QtCore import Qt
from  typing import Dict, List, Tuple, Callable
from controllers.help import (open_tutorials, report_issue, open_documentation,
                              check_updates, show_about)
from controllers.file_menu_controller import ProjectController

# main class for menubar
class MenuBarModule(QMenuBar):
    def __init__(self, main_window):
        super().__init__(main_window)
        self.main_window = main_window
        # self.project_controller = ProjectController(self.main_window)
        # export_results, export_visualization = self.project_controller.export_results, self.project_controller.export_visualization
        # Use the main window's project controller instead of creating a new one
        self.project_controller = main_window.project_controller

        # clear existing menu
        self.clear()

        #set style
        self._set_style()

        # Create menus
        self.create_advanced_menubar()

        # Ensure the proper spacingand margins
        self.setContentsMargins(0, 0, 0, 0)

       # Set style
    def _set_style(self) -> None:
        self.setStyleSheet("""
            QMenuBar {
                background-color: #34495E;
                color: #ECF0F1;
                spacing: 10px;
                padding: 0px;
                margin: 0px;
            }
            QMenuBar::item {
                spacing: 10px;
                padding: 5px 10px;
                background-color: transparent;
                margin: 0px;
            }
            QMenuBar::item:selected {
                background-color: #3498DB;
            }
            QMenu {
                background-color: #34495E;
                color: #ECF0F1;
                border: 1px solid #3498DB;
            }
            QMenu::item:selected {
                background-color: #3498DB;
            }
        """)
        
        # Ensure proper spacing and margins
        self.setContentsMargins(0, 0, 0, 0)

    def create_advanced_menubar(self):
        """Create the menu bar with improved working"""

        self.menu_structure = {
             '&File': {
                # 'Project': [
                #     ('New Project', 'Ctrl+N', self.project_controller.new_project),
                #     ('Open Project', 'Ctrl+O', lambda: self.project_controller.open_project(False)),
                #     ('Open in New Window', 'Ctrl+Shift+O', lambda: self.project_controller.open_project(True)),
                #     ('Save Project', 'Ctrl+S', self.project_controller.save_project),
                #     ('Save Project As...', 'Ctrl+Shift+S', lambda: self.project_controller.save_project(save_as=True)),
                #     ('Close Project', 'Ctrl+F4', self.project_controller.closed_project)
                # ],
                'Project': [
                    ('New Project Window', 'Ctrl+Shift+N', self.project_controller.new_project_in_new_window),
                    ('Open in New Window', 'Ctrl+Shift+O', lambda: self.project_controller.open_project(True)),
                    ('Save Project', 'Ctrl+S', self.project_controller.save_project),
                    ('Save As...', 'Ctrl+Shift+S', lambda: self.project_controller.save_project(True)),
                    ('Close Project', 'Ctrl+W', self.project_controller.closed_project)
                ],
                # 'Import/Export': [
                #     ('Import Data', 'Ctrl+I', self.main_window.import_data),
                # ],
                'Exit': [
                    ('Exit Application', 'Alt+F4', self.main_window.close)
                ]
            },
            '&Tools': {
                'Plugins': [
                    ('Plugin Store', 'Ctrl+Shift+P', self.main_window.open_plugin_store)
                ],
                'Preferences': [
                    ('Settings', 'Ctrl+,', self.main_window.open_settings)
                ]
            },
            # '&View': {
            #     'Widgets': [
            #         ('Show Instructions', 'Ctrl+H', self.main_window.toggle_instructions_widget),
            #         ('Show Control Panel', 'Ctrl+B', self.main_window.toggle_control_panel)
            #     ]
            # },
            '&Help': {
                'Documentation': [
                    ('User Guide', 'F1', open_documentation),
                    ('Tutorials', 'Shift+F1', open_tutorials)
                ],
                'Support': [
                    ('Check Updates', 'Ctrl+U', check_updates),
                    ('Report Issue', 'Ctrl+Shift+I', report_issue)
                ],
                'About': [
                    ('About Application', 'Ctrl+F1', show_about),
                ]
            }
        }
        # Create menus from structure
        for menu_name, submenu_dict in self.menu_structure.items():
            menu = self.addMenu(menu_name)
            self.create_submenu(menu, submenu_dict)

    def create_submenu(self, parent_menu: QMenu, submenu_dict: Dict[str, List[Tuple[str, str, Callable]]]):
        """Create submenu items with improved error handling and shortcut management"""
        for submenu_name, actions in submenu_dict.items():
            submenu = QMenu(submenu_name, self.main_window)
            for action_name, shortcut, method in actions:
                    action = QAction(action_name, self.main_window)
                    if shortcut:
                        try: 
                            action.setShortcut(shortcut)
                            # set shortcut context to application-wide
                            action.setShortcutContext(Qt.WindowShortcut)
                        except Exception as e:
                            print(f"Error setting shortcut for {action_name}: {e}")
                    
                    action.triggered.connect(method)
                    submenu.addAction(action)
            
            # add submenu to parent menu
            parent_menu.addMenu(submenu)
    
        # def _populate_recent_menu(self, menu):
        #     recent_projects = self.main_window.project_controller.get_recent_projects()
        #     if not recent_projects:
        #         menu.addAction("No recent projects").setEnabled(False)
        #         return
            
        #     for project_path in recent_projects[:10]:
        #         action = menu.addAction(os.path.basename(project_path))
        #         action.triggered.connect(lambda checked, p=project_path: 
        #             self.main_window.project_controller._load_project_from_file(p, False))