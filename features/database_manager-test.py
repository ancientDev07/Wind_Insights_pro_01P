import sqlite3
import pandas as pd
from datetime import datetime

class DatabaseManager:
    def __init__(self, db_path="test_wind.db"):
        self.connection = sqlite3.connect(db_path)
        self.init_database()
    
    def init_database(self):
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                created_date TIMESTAMP
            )
        """)
        self.connection.commit()
    
    def create_project(self, name: str) -> int:
        cursor = self.connection.execute(
            "INSERT INTO projects (name, created_date) VALUES (?, ?)",
            [name, datetime.now()]
        )
        self.connection.commit()
        return cursor.lastrowid
    
    def create_project_table(self, project_id: int, columns: list):
        table_name = f"project_{project_id}_data"
        col_defs = ["id INTEGER PRIMARY KEY", "wtg_id TEXT NOT NULL"]
        
        for col in columns:
            clean_col = col.replace(' ', '_').lower()
            col_defs.append(f"{clean_col} TEXT")
        
        sql = f"CREATE TABLE {table_name} ({', '.join(col_defs)})"
        self.connection.execute(sql)
        self.connection.commit()
        return table_name