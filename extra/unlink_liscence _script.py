# # Test by deleting these files
# import os
# from pathlib import Path
# base_path = Path(os.getenv('APPDATA')) / 'Wind Data Insight Pro'
# (base_path / 'agreement_accepted').unlink(missing_ok=True)
# (base_path / 'setup_complete').unlink(missing_ok=True)

# complete_license_reset.py
import os
import winreg
from pathlib import Path

def clean_files():
    """Remove license files"""
    base_path = Path(os.getenv('APPDATA')) / 'Wind Data Insight Pro'
    files = ['agreement_accepted', 'setup_complete', 'license.json', 'license_key.txt']
    
    for file_name in files:
        (base_path / file_name).unlink(missing_ok=True)
        print(f"Removed: {file_name}")

def clean_registry():
    """Remove registry entries"""
    paths = [
        (winreg.HKEY_CURRENT_USER, r"Software\Wind Data Insight Pro"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Wind Data Insight Pro"),
    ]
    
    for hkey, path in paths:
        try:
            winreg.DeleteKeyEx(hkey, path)
            print(f"Registry deleted: {path}")
        except:
            pass

if __name__ == "__main__":
    clean_files()
    clean_registry()
    print("Complete reset done. Run as administrator if registry cleanup failed.")
