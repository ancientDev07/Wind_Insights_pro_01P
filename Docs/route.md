WWIP_APP.py 
  → Creates: self.data_table_module = DataTableModule()
  → Passes to: CentralWidget(data_table_module=self.data_table_module)
  
CentralWidget
  → Adds to stack: stack_widget.addWidget(data_table_module)
  → Updates data: data_table_module.update_data_table(data)
  
ControlPanel
  → Also updates: main_window.central_widget.update_data_table(data)
✅ Data table is actively used and displays turbine data from DB

New:
┌─────────────────────────────────────────────────────────────┐
│ 1. PROJECT OPENED (WWIP_APP.py)                            │
│    - on_project_created_from_start(project_id, name)       │
│    - Sets: self.current_project_id = project_id            │
│    - Calls: file_handler.set_project_id(project_id)        │
│    - Calls: control_panel.project_id = project_id          │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. FILE_HANDLER (file_handler.py)                          │
│    - set_project_id(project_id)                            │
│    - Calls: load_project_from_database(project_id)         │
│    - Gets turbines: db_manager.get_turbines(project_id)    │
│    - Emits: turbine_ids_available.emit(turbines)           │
│    - Loads first turbine: load_turbine_data(turbines[0])   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. DATABASE_MANAGER (database_manager.py)                  │
│    - get_turbines(project_id)                              │
│      → SELECT DISTINCT wtg_id FROM ProjectData_{id}        │
│    - get_turbine_data(project_id, wtg_id)                  │
│      → SELECT * FROM ProjectData_{id} WHERE wtg_id=?       │
│    - Returns: pd.DataFrame                                  │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. CONTROL_PANEL (control_panel.py)                        │
│    - Receives signal: turbine_ids_available                │
│    - Calls: populate_turbine_dropdown(turbines)            │
│    - Receives signal: turbine_data_loaded                  │
│    - Calls: handle_data_loaded(data)                       │
│    - Sets: self.current_data = data                        │
│    - Calls: main_window.central_widget.update_data_table() │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 5. CENTRAL_WIDGET (central_widget.py)                      │
│    - update_data_table(data)                               │
│    - Calls: data_table_module.update_data_table(data)      │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 6. DATA_TABLE_MODULE (data_table_module.py)                │
│    - update_data_table(data) / update_data(data)           │
│    - Creates: PandasModel(data)                            │
│    - Sets: table.setModel(model)                           │
│    - Displays data in QTableView                           │
└─────────────────────────────────────────────────────────────┘

Key Points:

DB stores data in ProjectData_{project_id} table

FileHandler loads from DB and emits signals

ControlPanel receives signals and updates UI

CentralWidget passes data to DataTableModule

DataTableModule displays in QTableView