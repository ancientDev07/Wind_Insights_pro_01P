# Wind Data Insight Pro - SDI Implementation Status

## Current Architecture

### Process Model: **Single Process (NOT Multi-Process)**

┌─────────────────────────────────────────────┐
│ ONE Python Process (PID: 12345) │
│ │
│ ┌──────────────┐ │
│ │ Start Screen │ │
│ └──────┬───────┘ │
│ │ │
│ ┌──────▼───────┐ │
│ │ Main Window │ │
│ │ (WWIP_APP) │ │
│ └──────┬───────┘ │
│ │ │
│ ┌──────▼────────────────────────────────┐ │
│ │ Multiple Analysis Windows │ │
│ │ - VisualizationWindow │ │
│ │ - PowerCurveWindow │ │
│ │ - TemperatureAnalysisWindow │ │
│ │ - TimeSeriesAnalysisWindow │ │
│ └───────────────────────────────────────┘ │
│ │
│ All share SAME memory, SAME crash risk │
└─────────────────────────────────────────────┘


**Problem:** If one window crashes → **ENTIRE APP CRASHES**

---

## Files Modified for SDI Support

### 1. ✅ `views/start/start_screen.py` - MODIFIED
**Changes:**
- Added `import subprocess` and `sys`
- Modified `open_project_direct()` to launch subprocess
- Added instance check using `InstanceManager`
- Modified `_on_creation_finished()` to launch subprocess
- Fixed `project_id` undefined error

**Key Code:**
```python
def open_project_direct(self, path):
    from utils.instance_manager import InstanceManager
    mgr = InstanceManager()
    
    if mgr.is_project_open(path):
        QMessageBox.warning(self, "Already Open", 
            "This project is already open in another window")
        return
    
    subprocess.Popen([
        sys.executable,
        "project_instance.py",
        "--project", path
    ])


2. ✅ utils/instance_manager.py - CREATED (NEW)
Purpose: Track open projects and prevent duplicate opens

Features:

Creates lock files in ~/.wind_insight_pro/locks/

is_project_open() - checks if project already open

acquire_lock() - locks project file

release_lock() - unlocks on close

Cross-platform (Windows/Unix compatible)

code:

class InstanceManager:
    LOCK_DIR = Path.home() / '.wind_insight_pro' / 'locks'
    
    def is_project_open(self, project_path):
        lock_file = self.LOCK_DIR / f"{Path(project_path).stem}.lock"
        return lock_file.exists()

3. ✅ utils/window_manager.py - CREATED (NEW)
Purpose: Manage multiple analysis windows per turbine

Features:

Tracks windows by (turbine_id, window_type) tuple

get_or_create() - reuses existing window or creates new

Brings existing window to front instead of creating duplicate

Code:
class WindowManager:
    def __init__(self):
        self.windows = {}  # {(turbine_id, window_type): window_instance}
    
    def get_or_create(self, turbine_id, window_type, window_class, *args, **kwargs):
        key = (turbine_id, window_type)
        
        if key in self.windows and self.windows[key].isVisible():
            self.windows[key].raise_()
            self.windows[key].activateWindow()
            return self.windows[key]
        
        window = window_class(*args, **kwargs)
        self.windows[key] = window
        window.destroyed.connect(lambda: self.windows.pop(key, None))
        return window

4. ✅ views/components/home/control_panel.py - MODIFIED
Changes:

Added from utils.window_manager import WindowManager

Added self.window_manager = WindowManager() in __init__

Modified all window opening methods

Modified Methods:

def open_visualization(self):
    turbine_name = self.turbine_combo.currentText()
    params = CentralizedDataManager.get_standard_params(self.turbine_combo, self)
    params['project_id'] = self.project_id
    
    viz_window = self.window_manager.get_or_create(
        turbine_name,
        'visualization',
        VisualizationWindow,
        self.current_data,
        **params
    )
    viz_window.show()

5. ✅ views/visualization_components/visualization_window.py - MODIFIED
Changes:

Added closeEvent() method

def closeEvent(self, event):
    plt.close('all')
    gc.collect()
    event.accept()


6. ✅ views/visualization_components/power_curve_window.py - MODIFIED
Changes:

Added closeEvent() method

def closeEvent(self, event):
    event.accept()


7. ✅ views/visualization_components/temperature_comp.py - MODIFIED
Changes:

Added closeEvent() method

def closeEvent(self, event):
    event.accept()


8. ✅ views/time_series/Time_series_comp.py - MODIFIED
Changes:

Added closeEvent() method

def closeEvent(self, event):
    event.accept()


Files NOT Yet Created (Needed for Full SDI)
    ❌ launcher.py - NOT CREATED
    Purpose: Separate launcher process for start screen
    Status: Still using main_app.py (single process)
    
    Required Code:
    
    import sys
    import subprocess
    from PyQt5.QtWidgets import QApplication
    from views.start.start_screen import StartScreen
    
    class Launcher:
        def __init__(self):
            self.app = QApplication(sys.argv)
            self.start_screen = StartScreen()
            self.start_screen.project_selected.connect(self.launch_project_instance)
            self.start_screen.show()
        
        def launch_project_instance(self, project_path):
            subprocess.Popen([
                sys.executable,
                "project_instance.py",
                "--project", project_path
            ])
        
        def run(self):
            return self.app.exec_()
    
    if __name__ == '__main__':
        launcher = Launcher()
        sys.exit(launcher.run())


❌ project_instance.py - NOT CREATED
Purpose: Separate process for each project
Status: Referenced in start_screen.py but doesn't exist

Required Code:

import sys
import argparse
from PyQt5.QtWidgets import QApplication
from WWIP_APP import WWIPApp
from utils.instance_manager import InstanceManager

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--project', help='Project file path')
    parser.add_argument('--project-id', help='Project ID')
    parser.add_argument('--project-name', help='Project name')
    args = parser.parse_args()
    
    app = QApplication(sys.argv)
    
    # Set unique app ID for taskbar
    if sys.platform == 'win32':
        import ctypes
        app_id = f'WindDataInsightPro.Project.{args.project or args.project_id}'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
    
    # Acquire lock
    instance_mgr = InstanceManager()
    if args.project:
        if not instance_mgr.acquire_lock(args.project):
            return 1
    
    main_window = WWIPApp()
    
    # Load project
    if args.project:
        main_window.project_controller._load_project_from_file(args.project)
    elif args.project_id and args.project_name:
        main_window.on_project_created_from_start(int(args.project_id), args.project_name)
    
    # Release lock on exit
    app.aboutToQuit.connect(lambda: instance_mgr.release_lock(args.project))
    
    main_window.show()
    return app.exec_()

if __name__ == '__main__':
    sys.exit(main())

❌ utils/autosave_manager.py - NOT CREATED
Purpose: Per-instance autosave and crash recovery
Status: Not implemented

Required Code:

import json
import shutil
from pathlib import Path
from PyQt5.QtCore import QTimer
from datetime import datetime

class AutosaveManager:
    AUTOSAVE_DIR = Path.home() / '.wind_insight_pro' / 'autosave'
    INTERVAL = 300000  # 5 minutes
    
    def __init__(self, project_path, main_window):
        self.project_path = project_path
        self.main_window = main_window
        self.AUTOSAVE_DIR.mkdir(parents=True, exist_ok=True)
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.autosave)
        self.timer.start(self.INTERVAL)
    
    def autosave(self):
        if not self.project_path:
            return
        
        autosave_file = self.AUTOSAVE_DIR / f"{Path(self.project_path).stem}_autosave.wdip"
        
        try:
            shutil.copy2(self.project_path, autosave_file)
            
            meta_file = autosave_file.with_suffix('.meta')
            with open(meta_file, 'w') as f:
                json.dump({
                    'original': str(self.project_path),
                    'timestamp': str(datetime.now()),
                    'pid': os.getpid()
                }, f)
        except Exception as e:
            print(f"Autosave failed: {e}")


Threading Status
✅ Threads ARE Used (Limited Scope)
1. ProjectCreationThread (views/start/start_screen.py)

class ProjectCreationThread(QThread):
    def run(self):
        db.create_project_from_metadata(...)


Purpose: Prevent UI freeze during project creation
Scope: Only for project creation

2. Qt Event Loop (Built-in)

app.exec_()  # Main Qt event loop

Purpose: Handle UI events, signals, slots
Scope: All UI operations

Feature Comparison
Feature	Current (Single Process)	Target (Multi-Process SDI)
Process per project	❌ No - All in one	✅ Yes - Each separate
Crash isolation	❌ One crash kills all	✅ Independent crashes
Taskbar separation	❌ One icon for all	✅ Separate icons
Memory isolation	❌ Shared memory	✅ Isolated memory
Threading	✅ Yes (limited)	✅ Yes (per process)
Window management	✅ Yes (WindowManager)	✅ Yes (per process)
Duplicate prevention	✅ Yes (lock files)	✅ Yes (lock files)
Window-level SDI	✅ Yes (per turbine)	✅ Yes (per turbine)

What Currently Works
✅ Window-level SDI

Each turbine can have one window per analysis type

Prevents duplicate windows for same turbine

✅ Instance Tracking

Detects if project already open (via lock files)

Shows warning when trying to open duplicate

✅ Clean Window Closure

Proper cleanup on window close

Memory management (plt.close, gc.collect)

✅ Threading

Background project creation

Non-blocking UI operations

What's Missing for True SDI
❌ Process Isolation

Still single process, not separate processes per project

Crash in one project affects all projects

❌ Subprocess Launching

project_instance.py doesn't exist yet

launcher.py doesn't exist yet

❌ Autosave Per Instance

No crash recovery mechanism

No per-project autosave

❌ Lock Enforcement

Lock checking exists but not enforced on project load

No cleanup of stale locks

How to Test Current State
Check Process Count:

import psutil

for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
    if 'python' in proc.info['name'].lower():
        print(f"PID: {proc.info['pid']}, CMD: {proc.info['cmdline']}")

Current Result: ONE Python process
Target Result: MULTIPLE Python processes (one per project)

Next Steps to Complete SDI
Step 1: Create launcher.py
Separate launcher process

Keeps start screen open

Launches project instances

Step 2: Create project_instance.py
Each project in separate process

Acquire/release locks

Unique taskbar icons

Step 3: Create utils/autosave_manager.py
Per-instance autosave

Crash recovery

Stale lock cleanup

Step 4: Update Entry Point
Change from python main_app.py

To python launcher.py


File Structure
.
.
├── launcher.py              # ❌ NEW - Start screen process
├── project_instance.py      # ❌ NEW - Project process
├── WWIP_APP.py             # ✅ KEEP - Main window
├── main_app.py             # ⚠️ LEGACY - Will be replaced
├── utils/
│   ├── instance_manager.py  # ✅ NEW - File locking
│   ├── autosave_manager.py  # ❌ NEW - Autosave
│   └── window_manager.py    # ✅ NEW - Window management
├── views/
│   ├── start/
│   │   └── start_screen.py  # ✅ MODIFIED
│   ├── components/
│   │   └── home/
│   │       └── control_panel.py  # ✅ MODIFIED
│   └── visualization_components/
│       ├── visualization_window.py      # ✅ MODIFIED
│       ├── power_curve_window.py        # ✅ MODIFIED
│       └── temperature_comp.py          # ✅ MODIFIED
└── test.md                  # 📄 THIS FILE



summary
Current State: Enhanced single-process app with window-level SDI
Target State: True multi-process SDI like Microsoft Word
Progress: ~60% complete (window management done, process isolation pending)