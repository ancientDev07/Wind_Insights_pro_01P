import sqlite3
import pandas as pd
from datetime import datetime
from pathlib import Path
import os
from dotenv import load_dotenv
import models.scada_utils as su
from models.scada_utils import detect_turbine_column
# add at top of database_manager.py
from utils.datetime_utils import parse_and_normalize_timestamps, to_iso_string


load_dotenv()

class DatabaseManager:
    """Minimal DB Manager - Clean implementation"""

    _instance = None # singleton

    @classmethod
    def get_instance(cls, db_path=None):
        if cls._instance is None:
            cls._instance = cls(db_path)
        return cls._instance
    
    # def __init__(self, db_path=None):
    #     if db_path is None:
    #         db_path = os.getenv('DB_PATH', 'data/wind_insight.db')
        
    #     Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    #     self.connection = sqlite3.connect(db_path, check_same_thread=False, timeout=30)
        
    #     # Performance optimizations
    #     self.connection.execute("PRAGMA foreign_keys = ON")
    #     self.connection.execute("PRAGMA journal_mode=WAL")
    #     self.connection.execute("PRAGMA synchronous=NORMAL")
    #     self.connection.execute("PRAGMA cache_size=-64000")
        
    #     self.init_database()

    def __init__(self, db_path=None):
            if db_path is None:
                db_path = os.getenv('DB_PATH', 'data/wind_insight.db')
            
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
            self.connection = sqlite3.connect(db_path, check_same_thread=False, timeout=30)
            
            self.connection.execute("PRAGMA foreign_keys = ON")
            self.connection.execute("PRAGMA journal_mode=WAL")
            self.connection.execute("PRAGMA synchronous=NORMAL")
            self.connection.execute("PRAGMA cache_size=-64000")
            
            self.init_database()
    
    def init_database(self):
        """Create Projects master table"""
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS Projects (
                project_id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_name TEXT UNIQUE NOT NULL,
                location TEXT,
                company TEXT,
                capacity TEXT,
                model_name TEXT,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # New : Cordinate data table
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS CoordinateData (
            coord_id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            wtg_id TEXT NOT NULL,
            elevation REAL,
            hub_height REAL,
            latitude REAL,
            longitude REAL,
            easting REAL,
            northing REAL,
            FOREIGN KEY (project_id) REFERENCES Projects(project_id) ON DELETE CASCADE
        )
    """)
        
        # NEW: AD Reference data table
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS ADReferenceData (
                ad_id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                wind_speed REAL NOT NULL,
                power REAL NOT NULL,
                FOREIGN KEY (project_id) REFERENCES Projects(project_id) ON DELETE CASCADE
            )
        """)
        
        self.connection.execute("CREATE INDEX IF NOT EXISTS idx_coord_project ON CoordinateData(project_id)")
        self.connection.execute("CREATE INDEX IF NOT EXISTS idx_coord_wtg ON CoordinateData(wtg_id)")
        self.connection.execute("CREATE INDEX IF NOT EXISTS idx_ad_project ON ADReferenceData(project_id)")
        self.connection.commit()

    def create_project_from_metadata(self, metadata: dict, data_file: str, progress_callback=None):
        """Complete flow: metadata + data file → database"""
        
        if progress_callback:
            progress_callback("Creating project...")
        
        cursor = self.connection.execute("""
            INSERT INTO Projects (project_name, location, company, capacity, model_name)
            VALUES (?, ?, ?, ?, ?)
        """, [
            metadata.get("name"),
            metadata.get("location", ""),
            metadata.get("company", ""),
            metadata.get("capacity", ""),
            metadata.get("model_name", "")
        ])
        self.connection.commit()
        project_id = cursor.lastrowid
        
        if progress_callback:
            progress_callback("Loading data file...")
        
        if data_file.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(data_file)
        else:
            df = pd.read_csv(data_file)
        
        wtg_column = self._detect_wtg_column(df)
        turbine_clusters = self._cluster_by_turbine(df, wtg_column)
        table_name = f"ProjectData_{project_id}"
        self._create_data_table(table_name, project_id, df.columns)
        
        if progress_callback:
            progress_callback("Saving turbine data...")
        
        self.connection.execute("BEGIN TRANSACTION")
        try:
            for wtg_id, turbine_data in turbine_clusters.items():
                self._save_turbine_data(table_name, project_id, wtg_id, turbine_data)
            self.connection.commit()
        except:
            self.connection.rollback()
            raise
        
        files = metadata.get("files") or {}
        
        if progress_callback:
            progress_callback("Saving coordinate data...")
        
        coord_file = files.get("coordinate")
        if coord_file:
            self.save_coordinate_data(project_id, coord_file)
        
        if progress_callback:
            progress_callback("Saving air density data...")
        
        ad_file = files.get("air_density")
        if ad_file:
            self.save_ad_reference_data(project_id, ad_file)
        
        return project_id, list(turbine_clusters.keys())


    # def _detect_wtg_column(self, df):
    #     """Auto-detect turbine ID column"""
    #     patterns = ['wtg', 'turbine', 'turbine_id', 'id']
        
    #     for col in df.columns:
    #         if col.lower() in patterns:
    #             return col
        
    #     for col in df.columns:
    #         if df[col].astype(str).str.upper().str.contains('WTG|T0|TURB', na=False).any():
    #             return col
    #     return None
    
    # NEW:
    def _detect_wtg_column(self, df):
        """Auto-detect turbine ID column"""
        return detect_turbine_column(df)
    
    def _cluster_by_turbine(self, df, wtg_column):
        """Cluster data by turbine"""
        if wtg_column:
            return {str(wtg): group for wtg, group in df.groupby(wtg_column)}
        return {"WTG_01": df}
    
    # def _create_data_table(self, table_name, project_id, columns):
    #     """Create dynamic data table"""
    #     col_defs = [
    #         "data_id INTEGER PRIMARY KEY AUTOINCREMENT",
    #         "project_id INTEGER NOT NULL",
    #         "wtg_id TEXT NOT NULL"
    #     ]
        
    #     for col in columns:
    #         clean_col = col.replace(' ', '_').replace('-', '_').lower()
    #         if clean_col not in ['data_id', 'project_id', 'wtg_id']:
    #             col_defs.append(f"{clean_col} REAL")
        
    #     col_defs.append("FOREIGN KEY (project_id) REFERENCES Projects(project_id) ON DELETE CASCADE")
        
    #     self.connection.execute(f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(col_defs)})")
    #     self.connection.execute(f"CREATE INDEX IF NOT EXISTS idx_{table_name}_project ON {table_name}(project_id)")
    #     self.connection.execute(f"CREATE INDEX IF NOT EXISTS idx_{table_name}_wtg ON {table_name}(wtg_id)")
    #     self.connection.commit()
    
    # def _save_turbine_data(self, table_name, project_id, wtg_id, data):
    #     """Bulk insert turbine data"""
    #     df = data.copy()
    #     df['project_id'] = project_id
    #     df['wtg_id'] = wtg_id
    #     df.columns = [col.replace(' ', '_').replace('-', '_').lower() for col in df.columns]
        
    #     columns = ', '.join(df.columns)
    #     placeholders = ', '.join(['?' for _ in df.columns])
    #     sql = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
        
    #     values = [tuple(row) for row in df.values]
    #     self.connection.executemany(sql, values)
    
    def _create_data_table(self, table_name, project_id, columns):
        col_defs = [
            "data_id INTEGER PRIMARY KEY AUTOINCREMENT",
            "project_id INTEGER NOT NULL",
            "wtg_id TEXT NOT NULL"
        ]
        for col in columns:
            clean = col.replace(' ', '_').replace('-', '_').lower()
            if clean not in ['data_id', 'project_id', 'wtg_id']:
                is_ts = any(kw in clean for kw in ['timestamp', 'datetime', 'date', 'time'])
                col_defs.append(f"{clean} {'TEXT' if is_ts else 'REAL'}")
        col_defs.append("FOREIGN KEY (project_id) REFERENCES Projects(project_id) ON DELETE CASCADE")
        self.connection.execute(f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(col_defs)})")
        self.connection.execute(f"CREATE INDEX IF NOT EXISTS idx_{table_name}_project ON {table_name}(project_id)")
        self.connection.execute(f"CREATE INDEX IF NOT EXISTS idx_{table_name}_wtg ON {table_name}(wtg_id)")
        self.connection.commit()


    def _save_turbine_data(self, table_name, project_id, wtg_id, data):
        df = data.copy()
        df['project_id'] = project_id
        df['wtg_id'] = wtg_id
        df.columns = [col.replace(' ', '_').replace('-', '_').lower() for col in df.columns]

        # Step 4 — parse timestamp columns → ISO string before DB insert
        for col in df.columns:
            if any(kw in col for kw in ['timestamp', 'datetime', 'date', 'time']):
                df[col] = to_iso_string(parse_and_normalize_timestamps(df[col]))

        def _to_sqlite(val):
            if val is None:
                return None
            try:
                if pd.isna(val):
                    return None
            except (TypeError, ValueError):
                pass
            if isinstance(val, pd.Timestamp):
                return val.isoformat()
            if hasattr(val, 'item'):
                return val.item()
            return val

        sql = f"INSERT INTO {table_name} ({', '.join(df.columns)}) VALUES ({', '.join(['?']*len(df.columns))})"
        values = [tuple(_to_sqlite(v) for v in row) for row in df.itertuples(index=False)]
        self.connection.executemany(sql, values)


    def get_turbine_data(self, project_id, wtg_id):
        table_name = f"ProjectData_{project_id}"
        df = pd.read_sql(
            f"SELECT * FROM {table_name} WHERE project_id = ? AND wtg_id = ?",
            self.connection, params=[project_id, wtg_id]
        )
        ts_cols = su.find_matching_columns(df, 'timestamp')
        if ts_cols:
            # ISO string → pd.Timestamp, no format guessing needed
            df[ts_cols[0]] = pd.to_datetime(df[ts_cols[0]], errors='coerce')
        return df.drop(columns=['project_id', 'wtg_id', 'data_id'], errors='ignore')


    def get_all_turbines_data(self, project_id):
        table_name = f"ProjectData_{project_id}"
        df = pd.read_sql(
            f"SELECT * FROM {table_name} WHERE project_id = ?",
            self.connection, params=[project_id]
        )
        ts_cols = su.find_matching_columns(df, 'timestamp')
        if ts_cols:
            df[ts_cols[0]] = pd.to_datetime(df[ts_cols[0]], errors='coerce')
        return df.drop(columns=['data_id'], errors='ignore')


    
    def save_coordinate_data(self, project_id, coord_file):
        """Save coordinate file to database"""
        
        df = pd.read_excel(coord_file) if coord_file.endswith('.xlsx') else pd.read_csv(coord_file)
        
        # Normalize: strip, lowercase, replace spaces with underscores
        df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
        
        # Auto-detect columns using scada_utils
        wtg_cols = su.find_matching_columns(df, 'turbine_id')
        elev_cols = su.find_matching_columns(df, 'elevation')
        hub_cols = su.find_matching_columns(df, 'hub_height')
        
        if not (wtg_cols and elev_cols and hub_cols):
            raise ValueError(f"Required columns not found. Available: {list(df.columns)}")
        
        wtg_col, elev_col, hub_col = wtg_cols[0], elev_cols[0], hub_cols[0]
        
        # Optional columns
        lat_cols = su.find_matching_columns(df, 'latitude') or []
        lon_cols = su.find_matching_columns(df, 'longitude') or []
        
        for _, row in df.iterrows():
            # Clean latitude/longitude: remove degree symbol and whitespace
            lat_value = None
            if lat_cols:
                lat_str = str(row[lat_cols[0]]).strip().replace('°', '')
                try:
                    lat_value = float(lat_str)
                except:
                    lat_value = None
            
            lon_value = None
            if lon_cols:
                lon_str = str(row[lon_cols[0]]).strip().replace('°', '')
                try:
                    lon_value = float(lon_str)
                except:
                    lon_value = None
            
            self.connection.execute("""
                INSERT INTO CoordinateData (project_id, wtg_id, elevation, hub_height, latitude, longitude)
                VALUES (?, ?, ?, ?, ?, ?)
            """, [
                project_id,
                str(row[wtg_col]).strip(),
                float(row[elev_col]),
                float(row[hub_col]),
                lat_value,
                lon_value
            ])
        self.connection.commit()

    # def save_ad_reference_data(self, project_id, ad_file):
    #     """Save AD reference file to database"""
    #     import pandas as pd
        
    #     df = pd.read_excel(ad_file) if ad_file.endswith('.xlsx') else pd.read_csv(ad_file)

    #     ws_cols = su.find_matching_columns(df, 'wind_speed')
    #     power_cols = su.find_matching_columns(df, 'power')
        
    #     if ws_cols not in df.columns or power_cols not in df.columns:
    #         raise ValueError("AD file must contain 'wind_speed' and 'power' columns")
        
    #     for _, row in df.iterrows():
    #         self.connection.execute("""
    #             INSERT INTO ADReferenceData (project_id, wind_speed, power)
    #             VALUES (?, ?, ?)
    #         """, [project_id, float(row['wind_speed']), float(row['power'])])
    #     self.connection.commit()


    # def get_coordinate_data(self, project_id):
    #     """Get coordinate data for project"""
    #     import logger
    #     try:
    #         df = pd.read_sql(f"SELECT * FROM CoordinateData WHERE project_id = ?", 
    #                         self.connection, params=[project_id])
    #         logger.info(f"DEBUG: Query returned {len(df)} rows for project_id {project_id}")
    #         if df.empty:
    #             logger.warning("DEBUG: CoordinateData table may be empty or project_id mismatch")
    #         return df
    #     except Exception as e:
    #         logger.error(f"Failed to get coordinate data: {e}")
    #         return pd.DataFrame()

    def get_coordinate_data(self, project_id):
        """Get coordinate data for project"""
        try:
            df = pd.read_sql(
                "SELECT * FROM CoordinateData WHERE project_id = ?",
                self.connection, params=[project_id]
            )
            return df
        except Exception as e:
            print(f"Failed to get coordinate data: {e}")
            return pd.DataFrame()


    def save_ad_reference_data(self, project_id, ad_file):
        """Save AD reference file to database"""
        import models.scada_utils as su
        
        print(f"DEBUG: Loading AD file: {ad_file}")
        df = pd.read_excel(ad_file) if ad_file.endswith('.xlsx') else pd.read_csv(ad_file)
        
        print(f"DEBUG: Original columns: {list(df.columns)}")
        
        # Normalize column names to lowercase
        df.columns = df.columns.str.strip().str.lower()
        
        print(f"DEBUG: Normalized columns: {list(df.columns)}")
        
        # Use scada_utils to find columns
        ws_cols = su.find_matching_columns(df, 'wind_speed')
        power_cols = su.find_matching_columns(df, 'power')
        
        print(f"DEBUG: Found wind_speed columns: {ws_cols}")
        print(f"DEBUG: Found power columns: {power_cols}")
        
        if not ws_cols or not power_cols:
            raise ValueError(f"Required columns not found. Available: {list(df.columns)}")
        
        # FIX: Use set to remove duplicates, then take first
        ws_col = list(set(ws_cols))[0] if ws_cols else None
        power_col = list(set(power_cols))[0] if power_cols else None
        
        print(f"DEBUG: Using wind_speed column: {ws_col}")
        print(f"DEBUG: Using power column: {power_col}")
        print(f"DEBUG: Inserting {len(df)} rows into ADReferenceData")
        
        for _, row in df.iterrows():
            self.connection.execute("""
                INSERT INTO ADReferenceData (project_id, wind_speed, power)
                VALUES (?, ?, ?)
            """, [project_id, float(row[ws_col]), float(row[power_col])])
        self.connection.commit()
        
        print(f"✓ Successfully saved {len(df)} AD reference points to database")
           
    # def get_coordinate_data(self, project_id, wtg_id=None):
    #     """Get coordinate data for project or specific turbine"""
    #     if wtg_id:
    #         query = "SELECT * FROM CoordinateData WHERE project_id = ? AND wtg_id = ?"
    #         return pd.read_sql(query, self.connection, params=[project_id, wtg_id])
    #     else:
    #         query = "SELECT * FROM CoordinateData WHERE project_id = ?"
    #         return pd.read_sql(query, self.connection, params=[project_id])

    def get_ad_reference_data(self, project_id):
        """Get AD reference data for project"""
        query = "SELECT wind_speed, power FROM ADReferenceData WHERE project_id = ? ORDER BY wind_speed"
        return pd.read_sql(query, self.connection, params=[project_id])
    
    def get_turbines(self, project_id):
        """Get turbine list for project"""
        table_name = f"ProjectData_{project_id}"
        cursor = self.connection.execute(f"SELECT DISTINCT wtg_id FROM {table_name} ORDER BY wtg_id")
        return [row[0] for row in cursor.fetchall()]
      
    # def get_turbine_data(self, project_id, wtg_id):
    #     """Get specific turbine data"""
    #     table_name = f"ProjectData_{project_id}"
    #     df= pd.read_sql(f"SELECT * FROM {table_name} WHERE project_id = ? AND wtg_id = ?", 
    #                       self.connection, params=[project_id, wtg_id] ,parse_dates=['timestamp'])
    #     return df.drop(columns=['project_id', 'wtg_id', 'data_id'], errors='ignore')
    
    # def get_all_turbines_data(self, project_id):
    #     """Get all turbine data from project"""
    #     table_name = f"ProjectData_{project_id}"
    #     df = pd.read_sql(f"SELECT * FROM {table_name} WHERE project_id = ?", 
    #                      self.connection, params=[project_id],parse_dates=['timestamp'])
    #     return df.drop(columns=['data_id'], errors='ignore')

    # def get_turbine_data(self, project_id, wtg_id):
    #     """Get specific turbine data"""
    #     table_name = f"ProjectData_{project_id}"
    #     df = pd.read_sql(f"SELECT * FROM {table_name} WHERE project_id = ? AND wtg_id = ?", 
    #                       self.connection, params=[project_id, wtg_id])
    #     ts_cols = su.find_matching_columns(df, 'timestamp')
    #     if ts_cols:
    #         df[ts_cols[0]] = pd.to_datetime(df[ts_cols[0]], errors='coerce', dayfirst=True)
    #     return df.drop(columns=['project_id', 'wtg_id', 'data_id'], errors='ignore')
    
    # def get_all_turbines_data(self, project_id):
    #     """Get all turbine data from project"""
    #     table_name = f"ProjectData_{project_id}"
    #     df = pd.read_sql(f"SELECT * FROM {table_name} WHERE project_id = ?", 
    #                      self.connection, params=[project_id])
    #     ts_cols = su.find_matching_columns(df, 'timestamp')
    #     if ts_cols:
    #         df[ts_cols[0]] = pd.to_datetime(df[ts_cols[0]], errors='coerce')
    #     return df.drop(columns=['data_id'], errors='ignore')
    
    # def close(self):
    #     if self.connection:
    #         self.connection.close()

    def replace_project_data(self, project_id: int, file_path: str) -> list:
        """Delete existing SCADA data for project and re-import from new file."""
        
        # Load new file
        if file_path.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file_path)
        else:
            df = pd.read_csv(file_path)
        
        table_name = f"ProjectData_{project_id}"
        
        # Check table exists
        cursor = self.connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            [table_name]
        )
        table_exists = cursor.fetchone() is not None
        
        wtg_column = self._detect_wtg_column(df)
        turbine_clusters = self._cluster_by_turbine(df, wtg_column)
        
        self.connection.execute("BEGIN TRANSACTION")
        try:
            if table_exists:
                # Wipe existing data
                self.connection.execute(f"DELETE FROM {table_name} WHERE project_id = ?", [project_id])
            else:
                # Table never existed — create it fresh
                self._create_data_table(table_name, project_id, df.columns)
            
            for wtg_id, turbine_data in turbine_clusters.items():
                self._save_turbine_data(table_name, project_id, wtg_id, turbine_data)
            
            # Update last_modified on the project
            self.connection.execute(
                "UPDATE Projects SET last_modified = ? WHERE project_id = ?",
                [datetime.now().isoformat(), project_id]
            )
            self.connection.commit()
        except Exception:
            self.connection.rollback()
            raise
        
        return list(turbine_clusters.keys())

    def close(self):
        if self.connection:
            self.connection.close()
            self.connection = None
            DatabaseManager._instance = None  # ← reset so next get_instance() reopens cleanly