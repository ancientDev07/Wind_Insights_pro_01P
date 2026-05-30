# Database Layer Analysis
Based on your workspace, here's a comprehensive scan of the database layer:

🗄️ Core Database Components
## Main Database Manager
DatabaseManager — Central database operations handler
__init__() — Initialize with SQLite connection, set PRAGMA optimizations (WAL mode, foreign keys, cache)
init_database() — Create master Projects table + CoordinateData + ADReferenceData tables
create_project_from_metadata() — Complete flow: metadata + data file → database
_detect_wtg_column() — Auto-detect turbine ID column
_cluster_by_turbine() — Group data by turbine
_create_data_table() — Create dynamic ProjectData_{project_id} table with foreign keys
_save_turbine_data() — Bulk insert with executemany()
get_turbines() — Query distinct turbines for a project
get_turbine_data() — Load specific turbine data
get_all_turbines_data() — Load all turbines for a project
save_coordinate_data() — Save coordinate file to DB
save_ad_reference_data() — Save air density reference data to DB
get_coordinate_data() — Retrieve coordinate data
get_ad_reference_data() — Retrieve AD reference data
close() — Close connection
## Batch Processor
BatchProcessor — Bulk operations handler
save_all_turbines() — Save multiple turbines in single transaction with rollback support
## Async Database Worker
#### AsyncDBWorker — PyQt5 QThread for non-blocking DB ops
* Emits: progress, success, error signals
* Used in project creation flow to prevent UI freezing

📊 Database Schema

Master Table: Projects:
CREATE TABLE Projects (
    project_id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_name TEXT UNIQUE NOT NULL,
    location TEXT,
    company TEXT,
    capacity TEXT,
    model_name TEXT,
    created_date TIMESTAMP,
    last_modified TIMESTAMP
)

Master Table: Projects
CREATE TABLE ProjectData_{id} (
    data_id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    wtg_id TEXT NOT NULL,
    [dynamic columns from CSV] REAL,
    FOREIGN KEY (project_id) REFERENCES Projects ON DELETE CASCADE
)
-- Indexes: idx_{table}_project, idx_{table}_wtg

CoordinateData:
CREATE TABLE CoordinateData (
    coord_id INTEGER PRIMARY KEY,
    project_id INTEGER,
    wtg_id TEXT,
    elevation REAL,
    hub_height REAL,
    latitude REAL,
    longitude REAL,
    FOREIGN KEY (project_id) REFERENCES Projects ON DELETE CASCADE
)

ADReferenceData:
CREATE TABLE ADReferenceData (
    ad_id INTEGER PRIMARY KEY,
    project_id INTEGER,
    wind_speed REAL,
    power REAL,
    FOREIGN KEY (project_id) REFERENCES Projects ON DELETE CASCADE
)
🔌 Database Integration Points
1. File Handler → Database
FileHandler — Signal coordinator
load_project_from_database() — Queries DB for turbines and emits signals
load_turbine_data() — Delegates to DatabaseManager.get_turbine_data()
Signals: turbine_ids_available, turbine_data_loaded, clustering_completed
2. Control Panel → Database
ControlPanel
load_from_database() — Loads project data from DB
Populates turbine dropdown from DB turbine list
Updates data table with selected turbine data
3. Main App → Database
WWIPApp
handle_project_created_from_start_screen() — Calls DatabaseManager.create_project_from_metadata()
on_project_created_from_start() — Orchestrates file handler and control panel updates
4. Report Controller → Database
ReportController
get_project_metadata() — Queries Projects table
get_available_turbines() — Calls db.get_turbines()
get_turbine_data() — Calls db.get_turbine_data()
5. Visualization Windows → Database
PowerCurveWindow
_load_files_from_database() — Auto-loads coordinate and AD data from DB
ComparisonPlotWindow
Similar DB loading capability
TurbineMapController — Loads coordinate data for map rendering
6. Dashboard → Database
UnifiedDashboard
_get_project_name() — Queries Projects table
prepare_dashboard_data() — Fetches turbine data from DB
🧪 Test & Debug Tools
Database Test Flow
DatabaseTestFlow — Testing & debugging helper
Full end-to-end test of project creation flow
Methods mirror DatabaseManager for validation
Database Viewer
DatabaseViewer — GUI tool to inspect DB
Browse projects, view turbines, display data in table
Useful for development and debugging
🔧 Configuration & Environment
Database Path
Default: wind_insight.db
Configurable via .env: DB_PATH=data/wind_insight.db

PRAGMA foreign_keys = ON          # Enforce referential integrity
PRAGMA journal_mode = WAL          # Write-Ahead Logging (concurrent reads)
PRAGMA synchronous = NORMAL        # Balanced safety/speed
PRAGMA cache_size = -64000         # 64MB cache


User Creates Project
    ↓
ProjectMetadataDialog + DataFile
    ↓
AsyncDBWorker.run()
    ↓
DatabaseManager.create_project_from_metadata()
    ├─→ Insert into Projects table → auto-increment project_id
    ├─→ Load CSV/Excel file
    ├─→ Detect turbine column
    ├─→ Cluster by turbine
    ├─→ Create ProjectData_{id} table
    ├─→ Batch insert all turbine data (executemany)
    ├─→ Save coordinate file → CoordinateData table
    └─→ Save AD reference file → ADReferenceData table
    ↓
FileHandler.load_project_from_database()
    ├─→ Query turbines: SELECT DISTINCT wtg_id
    ├─→ Emit turbine_ids_available signal
    └─→ Load first turbine data
    ↓
ControlPanel.load_from_database()
    ├─→ Populate dropdown from turbine list
    ├─→ Update data table with first turbine
    └─→ Enable analysis buttons

📋 Summary
Component	Purpose	Status
DatabaseManager	Core DB engine	✅ Implemented
BatchProcessor	Bulk operations	✅ Implemented
AsyncDBWorker	Non-blocking ops	✅ Implemented
FileHandler integration	DB signal coordination	✅ Implemented
ControlPanel integration	UI ↔ DB sync	✅ Implemented
Report generation	DB query support	✅ Implemented
Visualization windows	DB data loading	✅ Implemented
Tests	Coverage	✅ Basic tests in tests

The database layer is production-ready with proper foreign keys, indexes, transactions, and performance optimizations (WAL mode, batch inserts, caching).