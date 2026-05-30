# register_filetype.py
"""
Windows file-type registration for .wdip files
Run with administrator privileges during installation
"""

import winreg
import sys
import os
from pathlib import Path

class FileTypeRegistrar:
    def __init__(self, extension=".wdip", prog_id="WindDataInsightPro.Project"):
        self.extension = extension
        self.prog_id = prog_id
        self.app_name = "Wind Data Insight Pro"
        
    def register(self, mode="production"):
        """Register file type association"""
        try:
            if mode == "development":
                exe_path = sys.executable
                command = f'"{exe_path}" "{os.path.abspath("main_app.py")}" --project "%1"'
            else:
                exe_path = os.path.join(os.path.dirname(sys.executable), "WindDataInsightPro.exe")
                command = f'"{exe_path}" --project "%1"'
            
            icon_path = os.path.abspath("resources/app_icon/wwip_file.ico")
            
            # Register extension
            with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, self.extension) as key:
                winreg.SetValue(key, "", winreg.REG_SZ, self.prog_id)
            
            # Register ProgID
            with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, self.prog_id) as key:
                winreg.SetValue(key, "", winreg.REG_SZ, f"{self.app_name} Project")
            
            # Set icon
            with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, f"{self.prog_id}\\DefaultIcon") as key:
                winreg.SetValue(key, "", winreg.REG_SZ, f"{icon_path},0")
            
            # Register open command
            with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, f"{self.prog_id}\\shell\\open\\command") as key:
                winreg.SetValue(key, "", winreg.REG_SZ, command)
            
            # Notify shell of changes
            import ctypes
            ctypes.windll.shell32.SHChangeNotify(0x08000000, 0x0000, None, None)
            
            print(f"✓ Registered {self.extension} with {self.app_name}")
            return True
            
        except PermissionError:
            print("✗ Error: Run as Administrator")
            return False
        except Exception as e:
            print(f"✗ Registration failed: {e}")
            return False
    
    def unregister(self):
        """Remove file type association"""
        try:
            # Remove extension key
            try:
                winreg.DeleteKey(winreg.HKEY_CLASSES_ROOT, self.extension)
            except FileNotFoundError:
                pass
            
            # Remove ProgID keys recursively
            self._delete_key_recursive(winreg.HKEY_CLASSES_ROOT, self.prog_id)
            
            # Notify shell
            import ctypes
            ctypes.windll.shell32.SHChangeNotify(0x08000000, 0x0000, None, None)
            
            print(f"✓ Unregistered {self.extension}")
            return True
            
        except Exception as e:
            print(f"✗ Unregistration failed: {e}")
            return False
    
    def _delete_key_recursive(self, root, path):
        """Recursively delete registry key"""
        try:
            with winreg.OpenKey(root, path, 0, winreg.KEY_ALL_ACCESS) as key:
                subkeys = []
                i = 0
                while True:
                    try:
                        subkeys.append(winreg.EnumKey(key, i))
                        i += 1
                    except OSError:
                        break
                
                for subkey in subkeys:
                    self._delete_key_recursive(root, f"{path}\\{subkey}")
            
            winreg.DeleteKey(root, path)
        except FileNotFoundError:
            pass
    
    def verify(self):
        """Verify registration is active"""
        try:
            with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, self.extension) as key:
                prog_id = winreg.QueryValue(key, "")
                if prog_id == self.prog_id:
                    print(f"✓ {self.extension} → {self.prog_id}")
                    
                    with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, f"{self.prog_id}\\shell\\open\\command") as cmd_key:
                        command = winreg.QueryValue(cmd_key, "")
                        print(f"✓ Command: {command}")
                    
                    return True
        except FileNotFoundError:
            print(f"✗ {self.extension} not registered")
            return False
        except Exception as e:
            print(f"✗ Verification failed: {e}")
            return False


# register_filetype.py - UPDATE main() function only

def main():
    """CLI interface for file type registration"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Register .wdip file type")
    parser.add_argument("action", nargs='?', choices=["register", "unregister", "verify"], 
                       help="Action to perform")
    parser.add_argument("--mode", choices=["development", "production"], 
                       default="development", help="Registration mode")
    
    args = parser.parse_args()
    
    registrar = FileTypeRegistrar()
    
    # Interactive mode if no action provided
    if not args.action:
        print("\n=== Wind Data Insight Pro File Type Registration ===\n")
        print("1. Register (Development)")
        print("2. Register (Production)")
        print("3. Verify")
        print("4. Unregister")
        choice = input("\nSelect option (1-4): ").strip()
        
        if choice == "1":
            registrar.register(mode="development")
        elif choice == "2":
            registrar.register(mode="production")
        elif choice == "3":
            registrar.verify()
        elif choice == "4":
            registrar.unregister()
        else:
            print("Invalid choice")
        return
    
    # CLI mode
    if args.action == "register":
        registrar.register(mode=args.mode)
    elif args.action == "unregister":
        registrar.unregister()
    elif args.action == "verify":
        registrar.verify()



if __name__ == "__main__":
    main()
