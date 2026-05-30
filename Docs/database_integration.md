# DATABASE INTEGRATION CHANGES - TECHNICAL DOCUMENTATION

## Overview

This document explains the database integration changes made to Wind Data Insight Pro (WWIP) to replace file-based data storage with SQLite database storage for improved performance and scalability.

---

## 1. ARCHITECTURE CHANGES

### 1.1 Previous Architecture (File-Based)

User Upload → FileHandler → Cluster by Turbine → Save CSV Files → Load from Files

### 1.2 New Architecture (Database-Based)

User Upload → DatabaseManager → Cluster by Turbine → Save to SQLite → Load from Database
↓
FileHandler (Signal Coordinator)
↓
Control Panel → Data Table

---

## 2. KEY COMPONENTS MODIFIED

### 2.1 DatabaseManager (`controllers/database/database_manager.py`)

``Purpose``: Central database operations handler

**Key Methods**:

- `create_project_from_metadata(metadata, data_file)` - Creates project and processes data file
- `get_turbines(project_id)` - Returns list of turbines for a project
- `get_turbine_data(project_id, wtg_id)` - Loads specific turbine data
- `_detect_wtg_column(df)` - Auto-detects turbine ID column
- `_cluster_by_turbine(df, wtg_column)` - Groups data by turbine

**Database Schema**:

```sql
-- Master Projects Table
CREATE TABLE Projects (
    project_id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_name TEXT UNIQUE NOT NULL,
    location TEXT,
    company TEXT,
    capacity TEXT,
    model_name TEXT,
    created_date TIMESTAMP,
    last_modified TIMESTAMP
);

-- Dynamic Project Data Tables (one per project)
CREATE TABLE ProjectData_{project_id} (
    data_id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    wtg_id TEXT NOT NULL,
    [dynamic columns based on data file],
    FOREIGN KEY (project_id) REFERENCES Projects(project_id)
);
```

## Performance Optimizations:

1. WAL (Write-Ahead Logging) mode for concurrent reads

2. Batch inserts with transactions

3. Indexed columns (project_id, wtg_id)

4. Cache size optimization (-64000 pages)

### 2.2 FileHandler (controllers/file_handler.py)

``Purpose``: Signal coordinator between database and UI

**Previous Role** : File loading, clustering, CSV saving
New Role: Database loading coordination, signal emission

**Key Changes**:
```
# OLD (File-based)
def load_turbine_data(self, turbine):
    turbine_data = pd.read_csv(f"output/{turbine}.csv")
    self.signals.turbine_data_loaded.emit(turbine_data)
 
# NEW (Database-based)
def load_turbine_data(self, turbine):
    turbine_data = self.db_manager.get_turbine_data(self.project_id, turbine)
    self.signals.turbine_data_loaded.emit(turbine_data)
```

**Signals**:

- `turbine_ids_available` - Emits list of turbines

- `turbine_data_loaded` - Emits turbine DataFrame

- `clustering_completed` - Emits turbine dictionary

- `status_update` - Status messages

- `error_occurred` - Error messages

### 2.3 Control Panel (`views/components/home/control_panel.py`)

``Purpose``: UI controller for data loading and visualization

**Key Changes**:

### 1. Removed direct database calls
```
Now uses FileHandler signals
```
### 2. Signal connections:

```
self.file_handler.signals.turbine_ids_available.connect(self.populate_turbine_dropdown)
self.file_handler.signals.turbine_data_loaded.connect(self.handle_data_loaded)
```

### 3. Dropdown connection:
```
self.turbine_combo.currentIndexChanged.connect(self.load_turbine_data)

def load_turbine_data(self):
    turbine = self.turbine_combo.currentText()
    if turbine and self.file_handler:
        self.file_handler.load_turbine_data(turbine)  # Delegates to FileHandler

```

### 2.4 WWIP_APP (`WWIP_APP.py`)

`Purpose`: Main application window

**Key Changes**:

1. Project creation handler:

```
def on_project_created_from_start(self, project_id, project_name):
    self.current_project_id = project_id

    # CRITICAL: Set project_id in file_handler
    if hasattr(self, 'file_handler'):
        self.file_handler.set_project_id(project_id)

    # FileHandler automatically loads turbines and emits signals

2.Opening existing projects:

def on_project_selected_from_start(self, project_path):
    with open(project_path, 'r') as f:
        project_data = json.load(f)

    project_id = project_data.get("db_id")
    if project_id:
        self.on_project_created_from_start(project_id, project_name)
```

### 2.5 Start Screen (views/start/start_screen.py)

`Purpose`: Project creation and recent projects

**Key Changes**:

1. Project creation flow:
```
def handle_new_project(self, template_type):
    # Get metadata from dialog
    metadata = dialog.get_metadata()
    data_file = metadata.get("files", {}).get("data")

    # Create in database
    db = DatabaseManager()
    project_id, turbines = db.create_project_from_metadata(metadata, data_file)

    # Save .wdip file
    project_data = {
        "metadata": metadata,
        "db_id": project_id,
        "created_date": datetime.now().isoformat()
    }
    with open(file_path, 'w') as f:
        json.dump(project_data, f, indent=4)

    # Add to recent projects
    self.recent_manager.add_recent_project(file_path)

    # Emit signal
    self.project_created.emit(project_id, metadata['name'])
```

### 2.6 Project Controller (`controllers/file_menu_controller.py`)

`Purpose`: Project file management

**Key Changes**:
```
1. Support both old and new project formats:

def _validate_project_data(self, project_data):
    # New database format
    if "db_id" in project_data and "metadata" in project_data:
        return  # Valid new format

    # Old file format
    required_keys = ["metadata", "data", "analysis", "visualizations", "settings"]
    for key in required_keys:
        if key not in project_data:
            raise ValueError(f"Invalid project file: missing '{key}' section")

2. Route database projects correctly:

def _load_project_from_file(self, file_path):
    project_data = self._read_project_file(file_path)

    if "db_id" in project_data:
        # Database project - load from DB
        project_id = project_data["db_id"]
        self.main_window.on_project_created_from_start(project_id, project_name)
    else:
        # Old format - load from file
        self.project_opened.emit(project_name)
```


### 2.7 Data Table Module (`views/components/data_table_components/data_table_module.py`)

`Purpose`: Display data in table format

**Key `Fix`**:
```
class PandasModel(QAbstractTableModel):
    def __init__(self, data):
        super().__init__()
        self._data = data.reset_index(drop=True)  # Reset index to avoid mismatches
        self._string_cache = {}

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Vertical:
            if section < len(self._data):
                return str(section)  # Use section number, not DataFrame index
        return None
```
```
`Issue` Fixed: IndexError when DataFrame index didn't match row count
```

# 3. DATA FLOW DIAGRAMS

### 3.1 Project Creation Flow
```
Start Screen
    ↓
ProjectMetadataDialog (get metadata + data file)
    ↓
DatabaseManager.create_project_from_metadata()
    ├─→ Create Projects table entry
    ├─→ Load data file (CSV/Excel)
    ├─→ Auto-detect turbine column
    ├─→ Cluster by turbine
    ├─→ Create ProjectData_{id} table
    └─→ Batch insert turbine data
    ↓
Save .wdip file (metadata + db_id)
    ↓
Add to recent projects
    ↓
Emit project_created(project_id, name)
    ↓
WWIP_APP.on_project_created_from_start()
    ↓
FileHandler.set_project_id(project_id)
    ↓
FileHandler.load_project_from_database()
    ├─→ Get turbine list from DB
    ├─→ Emit turbine_ids_available signal
    └─→ Load first turbine data
    ↓
Control Panel receives signals
    ├─→ populate_turbine_dropdown()
    └─→ handle_data_loaded()
    ↓
Data Table renders
```
### 3.2 Turbine Selection Flow

```
User selects turbine from dropdown
    ↓
ControlPanel.load_turbine_data()
    ↓
FileHandler.load_turbine_data(turbine)
    ↓
DatabaseManager.get_turbine_data(project_id, turbine)
    ↓
SQL: SELECT * FROM ProjectData_{id} WHERE wtg_id = ?
    ↓
FileHandler emits turbine_data_loaded signal
    ↓
ControlPanel.handle_data_loaded()
    ├─→ Update self.current_data
    ├─→ Update data_table_module
    ├─→ Update central_widget
    └─→ Enable analysis buttons
    ↓
Data Table renders new turbine data
```

## 4. SIGNAL-SLOT ARCHITECTURE

### 4.1 Signal Flow
```
FileHandler (Emitter)
    ↓ turbine_ids_available
ControlPanel.populate_turbine_dropdown()
    ↓
Dropdown populated with turbine list
    ↓ currentIndexChanged
ControlPanel.load_turbine_data()
    ↓
FileHandler.load_turbine_data()
    ↓ turbine_data_loaded
ControlPanel.handle_data_loaded()
    ↓
DataTableModule.update_data_table()
    ↓
UI renders data
```

## 4.2 Key Signals


| **Signal**              | **Emitter**    | **Receiver**   | **Purpose**                |
|--------------------------|---------------|---------------|-----------------------------|
| turbine_ids_available    | FileHandler   | ControlPanel  | Populate dropdown           |
| turbine_data_loaded      | FileHandler   | ControlPanel  | Load turbine data           |
| clustering_completed     | FileHandler   | ControlPanel  | Turbine clustering done     |
| project_created          | StartScreen   | WWIP_APP      | New project created         |
| project_selected         | StartScreen   | WWIP_APP      | Open existing project       |




## 5. FILE STRUCTURE CHANGES

# 5.1 Old vs New Project File Formats
```
5.1 Old Project File (.wdip)
{
"metadata": {...},
"data": {
"datasets": [],
"active_dataset": {...}
},
"analysis": {...},
"visualizations": {...},
"settings": {...}
}
```

# 5.2 New Project File (.wdip)
```
{
"metadata": {
"name": "Project Name",
"created_date": "2025-12-29T18:00:00",
"location": "Site A",
"capacity": "100 MW"
},
"db_id": 1,
"files": {
"coordinate_file": "path/to/coordinates.xlsx",
"ad_reference_file": "path/to/ad_reference.xlsx"
},
"created_date": "2025-12-29T18:00:00"
}
```

### Key Differences:

1. Minimal structure (metadata + db_id only)

2. Data stored in database, not in .wdip file

3. File paths for auxiliary files (coordinates, AD reference)

## 6. PERFORMANCE IMPROVEMENTS


### 6.1 Database Optimizations

| Optimization   | Impact                      |
|----------------|-----------------------------|
| WAL mode       | Concurrent reads during writes |
| Batch inserts  | 10x faster data import     |
| Indexed columns| Fast turbine lookups       |
| Cache size     | Reduced disk I/O           |

### 6.2 UI Optimizations

| Optimization          | Impact                      |
|-----------------------|-----------------------------|
| Signal debouncing     | Prevents multiple redraws  |
| Lazy loading          | Only load selected turbine |
| String caching        | Faster table rendering     |
| Reset DataFrame index | Prevents IndexError        |



# 7. MIGRATION GUIDE

### 7.1 For Developers
To add new database features:

1. Add method to DatabaseManager

2. Add signal to FileHandlerSignals

3. Emit signal from FileHandler

4. Connect signal in ControlPanel.**init**

`Handle signal in ControlPanel method`

### Example:
```
# 1. DatabaseManager

def get*project_statistics(self, project_id):
return self.connection.execute("SELECT COUNT(\*) FROM ProjectData*?", [project_id])

# 2. FileHandlerSignals

class FileHandlerSignals(QObject):
statistics_loaded = pyqtSignal(dict)

# 3. FileHandler

def load_statistics(self):
stats = self.db_manager.get_project_statistics(self.project_id)
self.signals.statistics_loaded.emit(stats)

# 4. ControlPanel.**init**

self.file_handler.signals.statistics_loaded.connect(self.display_statistics)

# 5. ControlPanel

def display_statistics(self, stats):
self.stats_label.setText(f"Total records: {stats['count']}")
```

### 7.2 For Users
- `Old projects`: Still supported, will load from .wdip file
- `New projects`: Automatically use database storage
- `No action required`: System handles both formats

# 8. TROUBLESHOOTING


# 8. TROUBLESHOOTING

### 8.1 Common Issues

| Issue                      | Cause                                      | Fix                                                                 |
|----------------------------|--------------------------------------------|---------------------------------------------------------------------|
| Dropdown not populating    | project_id not set in FileHandler          | Ensure file_handler.set_project_id() is called in on_project_created_from_start() |
| Data table not rendering   | Signal not connected or parent reference wrong | Use self.window() instead of self.parent() to get main window      |
| IndexError in data table   | DataFrame index mismatch                   | Reset index in PandasModel: data.reset_index(drop=True)            |
| "No project loaded" error  | FileHandler.project_id is None             | Call file_handler.set_project_id(project_id) before loading data   |



### 9. TESTING CHECKLIST
- Create new project with data file
- Verify turbines appear in dropdown
- Select different turbines from dropdown
- Verify data table updates
- Close and reopen project
- Verify data loads from database
- Open old format project
- Verify backward compatibility
- Upload coordinate file
- Upload AD reference file
- Verify files saved in project



# 10. FUTURE ENHANCEMENTS

| Enhancement | Description |
|-------------|-------------|
| Multi-project support | Open multiple projects simultaneously |
| Data export | Export turbine data to CSV/Excel |
| Data filtering | Filter data before saving to database |
| Data versioning | Track changes to turbine data |
| Cloud sync | Sync database to cloud storage |
| Compression | Compress large datasets |
| Encryption | Encrypt sensitive project data |

# SUMMARY
The database integration replaces file-based storage with SQLite, improving:

- `Performance`: Faster data loading (no CSV parsing)

- `Scalability`: Handle larger datasets

- `Reliability`: ACID transactions, no file corruption

- `Maintainability`: Centralized data management
```
`Key Concept`: FileHandler acts as a signal coordinator, not a data loader. DatabaseManager handles all data operations, FileHandler emits signals, and ControlPanel responds to signals.
```
Last Updated: December 29, 2025
Version: 2.0 (Database Integration)