Now I see the issue. The open_project method in file_menu_controller.py needs to always open in a new instance. Here's the fix:

Replace the open_project method in file_menu_controller.py (around line 195):

def open_project(self, new_instance: bool = False) -> None:
    file_path = self._get_open_file_path()
    if not file_path:
        return
    
    if new_instance:
        self._open_in_new_instance(file_path)
    else:
        if not self._check_unsaved_changes():
            return
        self._load_project_from_file(file_path)

def _open_in_new_instance(self, file_path: str) -> None:
    import sys
    import subprocess
    
    try:
        python_exe = sys.executable
        main_script = os.path.join(os.path.dirname(__file__), '..', 'main_app.py')
        
        # Launch completely new process
        subprocess.Popen(
            [python_exe, main_script, '--open-project', file_path],
            creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0,
            start_new_session=True
        )
        self.show_status_message("Opening project in new window...")
    except Exception as e:
        self._show_error_dialog("Failed to open new instance", str(e))


Copy

Insert at cursor
Add to main_app.py at line 245 (in main() function):

def main():
    try:
        # Check for command-line project argument
        if '--open-project' in sys.argv:
            idx = sys.argv.index('--open-project')
            if idx + 1 < len(sys.argv):
                project_path = sys.argv[idx + 1]
                # Create new app instance and open project directly
                app = QApplication(sys.argv)
                main_window = WWIPApp()
                main_window.show()
                QTimer.singleShot(100, lambda: main_window.project_controller._load_project_from_file(project_path))
                return app.exec_()
        
        launcher = AppLauncher()
        return launcher.run()
    except Exception as e:
        if 'logger' in globals():
            logger.critical(f"Fatal error in main: {str(e)}", exc_info=True)
        else:
            print(f"Fatal error before logger initialization: {str(e)}")
            traceback.print_exc()
        return 1