import datetime
from utils.logger import logger
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QTreeWidget, QTreeWidgetItem, QLineEdit,QPushButton, QHBoxLayout, QHeaderView, QLabel, QMessageBox, QProgressDialog)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon
from typing import Tuple, Dict, Optional
import json
import  requests
from pathlib import Path
from typing import Dict

class PluginStoreDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Data Insight Pro - Plugin Store')
        self.setGeometry(300, 300, 700, 500)
        self.installed_plugins: Dict[str, str] = self._load_installed_plugins()
        self.setup_ui()
        logger.info("PluginStoreDialog initialized")

    def setup_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout()
        layout.setSpacing(10)  # Set spacing between widgets

        # search bar
        search_layout = QHBoxLayout()
        search_label = QLabel("Search....")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter plugin name or category: .....")
        self.search_input.textChanged.connect(self._filter_plugins)
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)

        # Plugin tree
        self.plugin_tree = QTreeWidget()
        self.plugin_tree.setHeaderLabels(['Plugin', 'Version', 'Status', 'Description'])
        self.plugin_tree.setColumnWidth(0, 200)  # Plugin name
        self.plugin_tree.setColumnWidth(1, 80)   # Version
        self.plugin_tree.setColumnWidth(2, 100)  # Status
        self.plugin_tree.header().setSectionResizeMode(3, QHeaderView.Stretch)  # Description
        self.plugin_tree.setAlternatingRowColors(True)
        self.plugin_tree.itemSelectionChanged.connect(self._update_button_states)
        self.populate_plugin_tree()

          # Buttons
        button_layout = QHBoxLayout()
        
        self.install_btn = QPushButton("Install Selected")
        self.install_btn.setIcon(QIcon.fromTheme('download'))
        self.install_btn.clicked.connect(self._install_selected_plugins)
        
        self.remove_btn = QPushButton("Remove Selected")
        self.remove_btn.setIcon(QIcon.fromTheme('edit-delete'))
        self.remove_btn.clicked.connect(self._remove_selected_plugins)
        
        self.refresh_btn = QPushButton("Refresh List")
        self.refresh_btn.setIcon(QIcon.fromTheme('view-refresh'))
        self.refresh_btn.clicked.connect(self._refresh_plugin_list)
        
        button_layout.addWidget(self.install_btn)
        button_layout.addWidget(self.remove_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.refresh_btn)

        layout.addWidget(self.plugin_tree)
        layout.addLayout(button_layout)

        self.setLayout(layout)
        self._update_button_states()
        logger.info("PluginStoreDialog UI setup complete")

    def _load_installed_plugins(self) -> Dict[str, dict]:
        """Load the list of installed plugins from the configuration file."""
        try:
            config_path = Path.home() / '.winddata' / 'plugins' / 'installed.json'
            if config_path.exists():
                with open(config_path, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"Failed to load installed plugins: {e}")
            return {}

    def _save_installed_plugins(self):
        """Save the current list of installed plugins to the configuration file."""
        try:
            config_path = Path.home() / '.winddata' / 'plugins' / 'installed.json'
            config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(config_path, 'w') as f:
                json.dump(self.installed_plugins, f, indent=4)
        except Exception as e:
            logger.error(f"Failed to save installed plugins: {e}")
            QMessageBox.warning(
                self,
                "Save Error",
                f"Failed to save plugin configuration: {str(e)}"
            )

    def populate_plugin_tree(self):
        """Populate the plugin tree with available plugins."""
        self.plugin_tree.clear()
        
        # In a real implementation, this would fetch from a server
        categories = {
            'Data Import': {
                'Database Connectors': [
                    {
                        'name': 'PostgreSQL Connector',
                        'version': '1.2.0',
                        'description': 'Connect and import data from PostgreSQL databases',
                        'id': 'postgresql-connector'
                    },
                    {
                        'name': 'MySQL Connector',
                        'version': '1.1.0',
                        'description': 'Connect and import data from MySQL databases',
                        'id': 'mysql-connector'
                    }
                ],
                'File Formats': [
                    {
                        'name': 'Advanced CSV Handler',
                        'version': '2.0.1',
                        'description': 'Enhanced CSV import with advanced options',
                        'id': 'advanced-csv'
                    }
                ]
            },
            'Analysis': {
                'Statistical': [
                    {
                        'name': 'Advanced Statistics',
                        'version': '1.3.0',
                        'description': 'Additional statistical analysis tools',
                        'id': 'advanced-stats'
                    }
                ],
                'Machine Learning': [
                    {
                        'name': 'Neural Network Models',
                        'version': '1.0.0',
                        'description': 'Neural network models for wind data analysis',
                        'id': 'neural-networks'
                    }
                ]
            },
            'Visualization': {
                'Charts': [
                    {
                        'name': '3D Wind Plots',
                        'version': '1.1.2',
                        'description': 'Advanced 3D visualization for wind data',
                        'id': '3d-wind-plots'
                    }
                ],
                'Maps': [
                    {
                        'name': 'Wind Map Overlays',
                        'version': '1.0.3',
                        'description': 'Geographic wind data visualization',
                        'id': 'wind-maps'
                    }
                ]
            }
        }

        for category, subcategories in categories.items():
            category_item = QTreeWidgetItem(self.plugin_tree, [category])
            category_item.setExpanded(True)
            
            for subcategory, plugins in subcategories.items():
                subcategory_item = QTreeWidgetItem(category_item, [subcategory])
                
                for plugin in plugins:
                    status = 'Installed' if plugin['id'] in self.installed_plugins else 'Available'
                    plugin_item = QTreeWidgetItem(subcategory_item, [
                        plugin['name'],
                        plugin['version'],
                        status,
                        plugin['description']
                    ])
                    plugin_item.setData(0, Qt.UserRole, plugin)

        logger.info("Plugin tree populated")

    def _filter_plugins(self, text: str):
        """Filter plugins based on search text."""
        text = text.lower()
        for i in range(self.plugin_tree.topLevelItemCount()):
            category_item = self.plugin_tree.topLevelItem(i)
            category_visible = False
            
            for j in range(category_item.childCount()):
                subcategory_item = category_item.child(j)
                subcategory_visible = False
                
                for k in range(subcategory_item.childCount()):
                    plugin_item = subcategory_item.child(k)
                    plugin_data = plugin_item.data(0, Qt.UserRole)
                    
                    # Check if plugin matches search
                    matches = (
                        text in plugin_data['name'].lower() or
                        text in plugin_data['description'].lower() or
                        text in category_item.text(0).lower() or
                        text in subcategory_item.text(0).lower()
                    )
                    
                    plugin_item.setHidden(not matches)
                    if matches:
                        subcategory_visible = True
                
                subcategory_item.setHidden(not subcategory_visible)
                if subcategory_visible:
                    category_visible = True
            
            category_item.setHidden(not category_visible)

    def _update_button_states(self):
        """Update button states based on selection."""
        selected_items = self.plugin_tree.selectedItems()
        has_installable = False
        has_removable = False
        
        for item in selected_items:
            plugin_data = item.data(0, Qt.UserRole)
            if plugin_data:  # Is a plugin item
                if plugin_data['id'] in self.installed_plugins:
                    has_removable = True
                else:
                    has_installable = True
        
        self.install_btn.setEnabled(has_installable)
        self.remove_btn.setEnabled(has_removable)

    def _install_selected_plugins(self):
        """Install selected plugins."""
        selected_items = self.plugin_tree.selectedItems()
        to_install = []
        
        for item in selected_items:
            plugin_data = item.data(0, Qt.UserRole)
            if plugin_data and plugin_data['id'] not in self.installed_plugins:
                to_install.append(plugin_data)
        
        if not to_install:
            return
            
        progress = QProgressDialog(
            "Installing plugins...",
            "Cancel",
            0,
            len(to_install),
            self
        )
        progress.setWindowModality(Qt.WindowModal)
        
        try:
            for i, plugin in enumerate(to_install):
                if progress.wasCanceled():
                    break
                    
                progress.setLabelText(f"Installing {plugin['name']}...")
                # Simulate installation
                self.installed_plugins[plugin['id']] = {
                    'version': plugin['version'],
                    'install_date': datetime.datetime.now().isoformat()
                }
                progress.setValue(i + 1)
            
            self._save_installed_plugins()
            self.populate_plugin_tree()
            self._update_button_states()
            
        except Exception as e:
            logger.error(f"Plugin installation failed: {e}")
            QMessageBox.warning(
                self,
                "Installation Error",
                f"Failed to install one or more plugins: {str(e)}"
            )
        finally:
            progress.close()

    def _remove_selected_plugins(self):
        """Remove selected plugins."""
        selected_items = self.plugin_tree.selectedItems()
        to_remove = []
        
        for item in selected_items:
            plugin_data = item.data(0, Qt.UserRole)
            if plugin_data and plugin_data['id'] in self.installed_plugins:
                to_remove.append(plugin_data)
        
        if not to_remove:
            return
            
        if QMessageBox.question(
            self,
            "Confirm Removal",
            f"Are you sure you want to remove {len(to_remove)} plugin(s)?",
            QMessageBox.Yes | QMessageBox.No
        ) != QMessageBox.Yes:
            return
            
        progress = QProgressDialog(
            "Removing plugins...",
            "Cancel",
            0,
            len(to_remove),
            self
        )
        progress.setWindowModality(Qt.WindowModal)
        
        try:
            for i, plugin in enumerate(to_remove):
                if progress.wasCanceled():
                    break
                    
                progress.setLabelText(f"Removing {plugin['name']}...")
                self.installed_plugins.pop(plugin['id'], None)
                progress.setValue(i + 1)
            
            self._save_installed_plugins()
            self.populate_plugin_tree()
            self._update_button_states()
            
        except Exception as e:
            logger.error(f"Plugin removal failed: {e}")
            QMessageBox.warning(
                self,
                "Removal Error",
                f"Failed to remove one or more plugins: {str(e)}"
            )
        finally:
            progress.close()

    def _refresh_plugin_list(self):
        """Refresh the plugin list from the server."""
        progress = QProgressDialog(
            "Refreshing plugin list...",
            "Cancel",
            0,
            100,
            self
        )
        progress.setWindowModality(Qt.WindowModal)
        
        try:
            progress.setValue(50)
            # In a real implementation, this would fetch from server
            self.populate_plugin_tree()
            progress.setValue(100)
            
        except Exception as e:
            logger.error(f"Plugin list refresh failed: {e}")
            QMessageBox.warning(
                self,
                "Refresh Error",
                f"Failed to refresh plugin list: {str(e)}"
            )
        finally:
            progress.close()
