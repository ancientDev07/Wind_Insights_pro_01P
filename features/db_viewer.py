import sqlite3
import pandas as pd
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import sys

class DatabaseViewer(QMainWindow):
    def __init__(self, db_path="test_wind_data.db"):
        super().__init__()
        self.db_path = db_path
        self.connection = sqlite3.connect(db_path)
        self.init_ui()
        self.load_projects()
    
    def init_ui(self):
        self.setWindowTitle("Database Viewer")
        self.setGeometry(100, 100, 1000, 700)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Project selection
        project_layout = QHBoxLayout()
        project_layout.addWidget(QLabel("Project:"))
        self.project_combo = QComboBox()
        self.project_combo.currentTextChanged.connect(self.load_project_data)
        project_layout.addWidget(self.project_combo)
        layout.addLayout(project_layout)
        
        # Turbine selection
        turbine_layout = QHBoxLayout()
        turbine_layout.addWidget(QLabel("Turbine:"))
        self.turbine_combo = QComboBox()
        self.turbine_combo.currentTextChanged.connect(self.load_turbine_data)
        turbine_layout.addWidget(self.turbine_combo)
        
        # Show all button
        show_all_btn = QPushButton("Show All Data")
        show_all_btn.clicked.connect(self.show_all_data)
        turbine_layout.addWidget(show_all_btn)
        layout.addLayout(turbine_layout)
        
        # Data table
        self.data_table = QTableWidget()
        layout.addWidget(self.data_table)
        
        # Info label
        self.info_label = QLabel("Select a project to view data")
        layout.addWidget(self.info_label)
    
    def load_projects(self):
        """Load all projects from database"""
        try:
            cursor = self.connection.execute("SELECT id, name FROM projects ORDER BY created_date DESC")
            projects = cursor.fetchall()
            
            self.project_combo.clear()
            for project_id, name in projects:
                self.project_combo.addItem(f"{name} (ID: {project_id})", project_id)
            
            if projects:
                self.info_label.setText(f"Found {len(projects)} projects")
            else:
                self.info_label.setText("No projects found in database")
                
        except Exception as e:
            self.info_label.setText(f"Error loading projects: {str(e)}")
    
    def load_project_data(self):
        """Load turbines for selected project"""
        if not self.project_combo.currentData():
            return
        
        project_id = self.project_combo.currentData()
        table_name = f"project_{project_id}_data"
        
        try:
            # Get distinct turbines
            cursor = self.connection.execute(f"SELECT DISTINCT wtg_id FROM {table_name} ORDER BY wtg_id")
            turbines = [row[0] for row in cursor.fetchall()]
            
            self.turbine_combo.clear()
            self.turbine_combo.addItems(turbines)
            
            # Get total record count
            cursor = self.connection.execute(f"SELECT COUNT(*) FROM {table_name}")
            total_records = cursor.fetchone()[0]
            
            self.info_label.setText(f"Project has {len(turbines)} turbines, {total_records} total records")
            
        except Exception as e:
            self.info_label.setText(f"Error loading project data: {str(e)}")
            self.turbine_combo.clear()
    
    def load_turbine_data(self):
        """Load data for selected turbine"""
        if not self.project_combo.currentData() or not self.turbine_combo.currentText():
            return
        
        project_id = self.project_combo.currentData()
        wtg_id = self.turbine_combo.currentText()
        table_name = f"project_{project_id}_data"
        
        try:
            # Load turbine data
            df = pd.read_sql(f"SELECT * FROM {table_name} WHERE wtg_id = ? ORDER BY id", 
                           self.connection, params=[wtg_id])
            
            self.display_dataframe(df)
            self.info_label.setText(f"Showing {len(df)} records for {wtg_id}")
            
        except Exception as e:
            self.info_label.setText(f"Error loading turbine data: {str(e)}")
    
    def show_all_data(self):
        """Show all data for selected project"""
        if not self.project_combo.currentData():
            return
        
        project_id = self.project_combo.currentData()
        table_name = f"project_{project_id}_data"
        
        try:
            # Load all project data
            df = pd.read_sql(f"SELECT * FROM {table_name} ORDER BY wtg_id, id", self.connection)
            
            self.display_dataframe(df)
            self.info_label.setText(f"Showing all {len(df)} records for project")
            
        except Exception as e:
            self.info_label.setText(f"Error loading all data: {str(e)}")
    
    def display_dataframe(self, df):
        """Display dataframe in table widget"""
        if df.empty:
            self.data_table.setRowCount(0)
            self.data_table.setColumnCount(0)
            return
        
        # Set table dimensions
        self.data_table.setRowCount(len(df))
        self.data_table.setColumnCount(len(df.columns))
        self.data_table.setHorizontalHeaderLabels(df.columns.tolist())
        
        # Fill table with data
        for i, row in df.iterrows():
            for j, value in enumerate(row):
                self.data_table.setItem(i, j, QTableWidgetItem(str(value)))
        
        # Auto-resize columns
        self.data_table.resizeColumnsToContents()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Check if database exists
    import os
    if not os.path.exists("test_wind_data.db"):
        QMessageBox.warning(None, "Database Not Found", 
                           "test_wind_data.db not found. Run the main test application first.")
        sys.exit()
    
    viewer = DatabaseViewer()
    viewer.show()
    sys.exit(app.exec_())
