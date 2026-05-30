import sys
import sqlite3
import pandas as pd
from pathlib import Path
from datetime import datetime
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

class DatabaseTestFlow:
    def __init__(self, db_path="test_wind_data.db"):
        self.db_path = db_path
        self.connection = sqlite3.connect(db_path)
        self.init_database()
    
    def init_database(self):
        """Initialize test database"""
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                created_date TIMESTAMP
            )
        """)
        self.connection.commit()
    
    def process_file_upload(self, file_path: str, project_name: str):
        """Test the complete flow"""
        print(f"Processing file: {file_path}")
        
        # Step 1: Load file
        if file_path.endswith('.xlsx'):
            df = pd.read_excel(file_path)
        else:
            df = pd.read_csv(file_path)
            
        print(f"Loaded {len(df)} rows, {len(df.columns)} columns")    

        # Step 2: Auto-detect WTG column
        wtg_column = self._detect_wtg_column(df)
        print(f"Detected WTG column: {wtg_column}")
        
        # Step 3: Auto-cluster
        turbine_clusters = self._cluster_by_turbine(df, wtg_column)
        print(f"Found {len(turbine_clusters)} turbines: {list(turbine_clusters.keys())}")
        
        # Step 4: Create project database
        project_id = self._create_project_database(project_name, df.columns)
        print(f"Created project {project_id}")
        
        # Step 5: Save clusters to database
        for wtg_id, turbine_data in turbine_clusters.items():
            self._save_turbine_to_db(project_id, wtg_id, turbine_data)
            print(f"Saved {len(turbine_data)} rows for {wtg_id}")
        
        return project_id, list(turbine_clusters.keys())
    
    def _detect_wtg_column(self, df):
        """Same detection logic"""
        turbine_patterns = ['wtg', 'turbine', 'turbine_id', 'id']
        
        for col in df.columns:
            if col.lower() in turbine_patterns:
                return col
        
        for col in df.columns:
            sample_values = df[col].astype(str).str.upper()
            if sample_values.str.contains('WTG|T0|TURB', na=False).any():
                return col
        return None
    
    def _cluster_by_turbine(self, df, wtg_column):
        """Same clustering logic"""
        if wtg_column:
            return {str(wtg_id): group for wtg_id, group in df.groupby(wtg_column)}
        else:
            return {"WTG_01": df}
    
    def _create_project_database(self, project_name: str, columns: list) -> int:
        """Create project and dynamic table"""
        cursor = self.connection.execute("""
            INSERT INTO projects (name, created_date) VALUES (?, ?)
        """, [project_name, datetime.now()])
        project_id = cursor.lastrowid
        
        # Create dynamic table
        table_name = f"project_{project_id}_data"
        column_defs = ["id INTEGER PRIMARY KEY", "wtg_id TEXT NOT NULL"]
        
        for col in columns:
            clean_col = col.replace(' ', '_').replace('-', '_').lower()
            column_defs.append(f"{clean_col} TEXT")
        
        create_sql = f"CREATE TABLE {table_name} ({', '.join(column_defs)})"
        self.connection.execute(create_sql)
        self.connection.commit()
        
        return project_id
    
    def _save_turbine_to_db(self, project_id: int, wtg_id: str, turbine_data: pd.DataFrame):
        """Save turbine data"""
        table_name = f"project_{project_id}_data"
        turbine_data = turbine_data.copy()
        turbine_data['wtg_id'] = wtg_id
        
        # Clean column names
        turbine_data.columns = [col.replace(' ', '_').replace('-', '_').lower() for col in turbine_data.columns]
        
        turbine_data.to_sql(table_name, self.connection, if_exists='append', index=False)
    
    def get_turbines(self, project_id: int):
        """Get available turbines"""
        table_name = f"project_{project_id}_data"
        cursor = self.connection.execute(f"SELECT DISTINCT wtg_id FROM {table_name}")
        return [row[0] for row in cursor.fetchall()]
    
    def get_turbine_data(self, project_id: int, wtg_id: str):
        """Get specific turbine data"""
        table_name = f"project_{project_id}_data"
        return pd.read_sql(f"SELECT * FROM {table_name} WHERE wtg_id = ?", 
                          self.connection, params=[wtg_id])

class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db_flow = DatabaseTestFlow()
        self.current_project_id = None
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("Database Flow Test")
        self.setGeometry(100, 100, 800, 600)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # File selection
        file_layout = QHBoxLayout()
        self.file_label = QLabel("No file selected")
        file_btn = QPushButton("Select Data File")
        file_btn.clicked.connect(self.select_file)
        file_layout.addWidget(self.file_label)
        file_layout.addWidget(file_btn)
        layout.addLayout(file_layout)
        
        # Process button
        self.process_btn = QPushButton("Process File to Database")
        self.process_btn.clicked.connect(self.process_file)
        self.process_btn.setEnabled(False)
        layout.addWidget(self.process_btn)
        
        # Turbine selection
        turbine_layout = QHBoxLayout()
        turbine_layout.addWidget(QLabel("Turbine:"))
        self.turbine_combo = QComboBox()
        self.turbine_combo.currentTextChanged.connect(self.load_turbine)
        turbine_layout.addWidget(self.turbine_combo)
        layout.addLayout(turbine_layout)
        
        # Data display
        self.data_table = QTableWidget()
        layout.addWidget(self.data_table)
        
        # Status
        self.status_label = QLabel("Ready")
        layout.addWidget(self.status_label)
    
    def select_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Data File", "", "Data Files (*.csv *.xlsx)")        
        if file_path:
            self.file_path = file_path
            self.file_label.setText(Path(file_path).name)
            self.process_btn.setEnabled(True)
    
    def process_file(self):
        if hasattr(self, 'file_path'):
            try:
                self.status_label.setText("Processing...")
                QApplication.processEvents()
                
                project_name = Path(self.file_path).stem
                project_id, turbines = self.db_flow.process_file_upload(self.file_path, project_name)
                
                self.current_project_id = project_id
                self.turbine_combo.clear()
                self.turbine_combo.addItems(turbines)
                
                self.status_label.setText(f"Processed! Found {len(turbines)} turbines")
                
            except Exception as e:
                self.status_label.setText(f"Error: {str(e)}")
                QMessageBox.critical(self, "Error", str(e))
    
    def load_turbine(self):
        if self.current_project_id and self.turbine_combo.currentText():
            try:
                wtg_id = self.turbine_combo.currentText()
                data = self.db_flow.get_turbine_data(self.current_project_id, wtg_id)
                
                # Display in table
                self.data_table.setRowCount(len(data))
                self.data_table.setColumnCount(len(data.columns))
                self.data_table.setHorizontalHeaderLabels(data.columns.tolist())
                
                for i, row in data.iterrows():
                    for j, value in enumerate(row):
                        self.data_table.setItem(i, j, QTableWidgetItem(str(value)))
                
                self.status_label.setText(f"Loaded {len(data)} rows for {wtg_id}")
                
            except Exception as e:
                self.status_label.setText(f"Error loading turbine: {str(e)}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    sys.exit(app.exec_())
