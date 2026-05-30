# # utils/instance_manager.py
# import sys
# import os
# import subprocess
# from typing import Optional
# from PyQt5.QtCore import QObject, pyqtSignal

# class InstanceManager(QObject):
#     """Manages multi-instance application lifecycle for SDI model"""
    
#     instance_launched = pyqtSignal(str)
    
#     def __init__(self):
#         super().__init__()
#         self.instances = []
    
#     def launch_new_instance(self, project_path: Optional[str] = None, show_start_screen: bool = False) -> bool:
#         """
#         Launch a new application instance
        
#         Args:
#             project_path: Path to project file to open in new instance
#             show_start_screen: If True, show start screen; if False and project_path provided, open directly
        
#         Returns:
#             bool: True if launch successful
#         """
#         try:
#             python_exe = sys.executable
#             main_script = os.path.join(os.path.dirname(__file__), '..', 'WWIP_APP.py')
            
#             args = [python_exe, main_script]
            
#             if project_path:
#                 args.extend(['--project', project_path])
#             elif show_start_screen:
#                 args.append('--start-screen')
            
#             process = subprocess.Popen(
#                 args,
#                 stdout=subprocess.PIPE,
#                 stderr=subprocess.PIPE,
#                 creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == 'win32' else 0
#             )
            
#             self.instances.append({
#                 'pid': process.pid,
#                 'project': project_path,
#                 'process': process
#             })
            
#             self.instance_launched.emit(project_path or "New Instance")
#             return True
            
#         except Exception as e:
#             print(f"Failed to launch instance: {e}")
#             return False
    
#     def get_active_instances(self):
#         """Return list of active instance PIDs"""
#         return [inst for inst in self.instances if inst['process'].poll() is None]

# utils/instance_manager.py
import sys
import os
import subprocess

class InstanceManager:
    @staticmethod
    def launch_new_instance(project_path=None, show_start_screen=False):
        try:
            args = [sys.executable, os.path.join(os.path.dirname(__file__), '..', 'main_app.py')]
            if project_path:
                args.extend(['--project', project_path])
            elif show_start_screen:
                args.append('--start-screen')
            
            subprocess.Popen(args, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == 'win32' else 0)
            return True
        except:
            return False
