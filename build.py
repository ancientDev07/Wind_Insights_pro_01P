import os
import sys
import shutil
import glob
import subprocess
import PyInstaller.__main__
from pathlib import Path
from typing import List, Dict, Set
import logging
from datetime import datetime
import pkg_resources
import importlib.util

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('build.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class BuildManager:
    def __init__(self):
        self.app_name = "Wind-Data-Insight-Pro"
        self.main_script = "main_app.py"
        self.build_dir = Path("build")
        self.dist_dir = Path("dist")
        self.logs_dir = Path("logs")
        self.required_dirs = {
            'config': ['.json', '.yaml', '.py'],
            'controllers': ['.py'],
            'data': ['.py'],
            'models': ['.py'],
            'utils': ['.json', '.py'],
            'views': ['.py'],
            'resources/app_icon': ['.ico', '.png'],
            'resources/direction': ['.png'],
            'resources/control_icons': ['.png'],
            'resources/icons': ['.ico', '.png'],
            'resources/images': ['.png', '.gif'],
            'resources/logos': ['.png'],
        }
        self.critical_files = [
            'config/config.json',
            'config/config.py',
            'main_app.py',
            'WWIP_APP.py',
            'resources/app_icon/wwip_file.ico',
            'resources/images/splash.png',
            'utils/valid_license_keys.json',
            'LICENSE',
        ]
        self.hidden_imports = [
            'qdarkstyle',
            'pandas',
            'numpy',
            'scipy',
            'sklearn',
            'pyqtgraph',
            'PyQt5',
            'PyQt5.QtCore',
            'PyQt5.QtWidgets', 
            'PyQt5.QtGui',
            'pandas.io.parsers',
            'pandas.io.parsers.readers',
            'pandas.io.common',
            'pandas.io.formats.style',
            'pandas.io.excel._xlsxwriter',
            'pandas.io.excel._openpyxl',
            'pandas._libs.parsers',
            'pandas._libs.tslibs',           # Add this
            'pandas._libs.tslibs.timedeltas', # Add this
            'pandas._libs.tslibs.timestamps', # Add this
            'pandas.tseries',                 # Add this
            'pandas.tseries.offsets',         # Add this
            'dateutil',                       # Add this
            'dateutil.parser',                # Add this
            'matplotlib',
            'matplotlib.backends.backend_qt5agg',
            'matplotlib.backends.backend_pdf',
            'matplotlib.backends.backend_svg',
            'matplotlib.figure',
            'matplotlib.dates', 
            'fontTools.ttLib',
            'fontTools.subset',
            'fontTools.subset.util',
            'pkg_resources.py2_warn'
        ]
        
        # Qt exclusions to prevent conflicts
        self.qt_exclusions = [
            'PyQt6',
            'PyQt6.QtCore',
            'PyQt6.QtWidgets',
            'PyQt6.QtGui',
            'PyQt6.QtOpenGL',
            'PyQt6.QtNetwork',
            'PyQt6.QtPrintSupport',
            'PyQt6.QtSvg',
            'PyQt6.QtTest',
            'PyQt6.QtXml',
            'PySide2',
            'PySide6',
            'tkinter',
            'tk',
            'jedi',
            'IPython'
        ]

    def create_installer(self) -> bool:
        """Create NSIS installer after build"""
        try:
            # Check if NSIS is installed
            nsis_paths = [
                r"C:\\Program Files (x86)\\NSIS\\makensis.exe",
                r"C:\\Program Files\\NSIS\\makensis.exe"
            ]

        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.warning("NSIS not found, skipping installer creation")

    def detect_qt_version(self) -> str:
        """Detect which Qt version is being used by the application."""
        logger.info("Detecting Qt version used by application...")
        
        # Try to determine from imports in main script
        try:
            with open(self.main_script, 'r') as f:
                content = f.read()
                
            if 'PyQt6' in content:
                logger.info("Detected PyQt6 usage in main script")
                return 'PyQt6'
            elif 'PyQt5' in content:
                logger.info("Detected PyQt5 usage in main script")
                return 'PyQt5'
            elif 'PySide6' in content:
                logger.info("Detected PySide6 usage in main script")
                return 'PySide6'
            elif 'PySide2' in content:
                logger.info("Detected PySide2 usage in main script")
                return 'PySide2'
                
        except Exception as e:
            logger.warning(f"Could not read main script: {e}")
        
        # Check what's actually importable
        qt_versions = ['PyQt5', 'PyQt6', 'PySide2', 'PySide6']
        available_versions = []
        
        for qt_ver in qt_versions:
            try:
                importlib.import_module(qt_ver)
                available_versions.append(qt_ver)
            except ImportError:
                pass
        
        if available_versions:
            logger.info(f"Available Qt versions: {available_versions}")
            # Default to PyQt5 if available (based on your hidden imports)
            if 'PyQt5' in available_versions:
                return 'PyQt5'
            else:
                return available_versions[0]
        
        logger.warning("No Qt version detected, defaulting to PyQt5")
        return 'PyQt5'

    def update_hidden_imports_for_qt(self, qt_version: str):
        """Update hidden imports based on detected Qt version."""
        logger.info(f"Updating hidden imports for {qt_version}")
        
        # Remove all Qt-related imports first
        self.hidden_imports = [imp for imp in self.hidden_imports 
                              if not any(qt in imp for qt in ['PyQt5', 'PyQt6', 'PySide2', 'PySide6'])]
        
        # Add appropriate Qt imports
        if qt_version == 'PyQt6':
            qt_imports = [
                'PyQt6',
                'PyQt6.QtCore',
                'PyQt6.QtWidgets', 
                'PyQt6.QtGui',
                'matplotlib.backends.backend_qt5agg',  # This often works for Qt6 too
            ]
            # Update exclusions to exclude other Qt versions
            self.qt_exclusions = [
                'PyQt5', 'PyQt5.QtCore', 'PyQt5.QtWidgets', 'PyQt5.QtGui',
                'PySide2', 'PySide6', 'tkinter', 'tk'
            ]
        elif qt_version == 'PyQt5':
            qt_imports = [
                'PyQt5',
                'PyQt5.QtCore',
                'PyQt5.QtWidgets', 
                'PyQt5.QtGui',
                'matplotlib.backends.backend_qt5agg',
            ]
            # Keep existing exclusions
        elif qt_version == 'PySide6':
            qt_imports = [
                'PySide6',
                'PySide6.QtCore',
                'PySide6.QtWidgets', 
                'PySide6.QtGui',
                'matplotlib.backends.backend_qt5agg',
            ]
            self.qt_exclusions = [
                'PyQt5', 'PyQt6', 'PySide2', 'tkinter', 'tk'
            ]
        elif qt_version == 'PySide2':
            qt_imports = [
                'PySide2',
                'PySide2.QtCore',
                'PySide2.QtWidgets', 
                'PySide2.QtGui',
                'matplotlib.backends.backend_qt5agg',
            ]
            self.qt_exclusions = [
                'PyQt5', 'PyQt6', 'PySide6', 'tkinter', 'tk'
            ]
        
        self.hidden_imports.extend(qt_imports)

    def verify_python_dependencies(self) -> bool:
        """Verify all required Python packages are installed."""
        logger.info("Verifying Python dependencies...")
        try:
            requirements_file = Path('requirements.txt')
            if not requirements_file.exists():
                logger.warning("requirements.txt not found, skipping dependency check")
                return True
                
            with open(requirements_file, 'r') as f:
                requirements = [
                    req.strip() 
                    for req in f.read().splitlines() 
                    if req.strip() and not req.startswith('#')
                ]
            
            missing_deps = []
            for req in requirements:
                try:
                    # Handle different requirement formats
                    package_name = req.split('==')[0].split('>=')[0].split('<=')[0].split('~=')[0].strip()
                    if package_name:
                        # Skip pyinstaller since we're already using it
                        if package_name.lower() == 'pyinstaller':
                            continue
                            
                        # Try importing the package
                        try:
                            importlib.import_module(package_name)
                        except ImportError:
                            # Some packages have different import names, try alternatives
                            alt_names = {
                                'pyqt5': 'PyQt5',
                                'pyqt6': 'PyQt6',
                                'scikit-learn': 'sklearn',
                                'pillow': 'PIL',
                                'pyqtchart': 'PyQt5.QtChart',
                                'pyinstaller': 'PyInstaller',
                                'python-dotenv': 'dotenv'
                            }
                            alt_name = alt_names.get(package_name.lower())
                            if alt_name:
                                importlib.import_module(alt_name)
                            else:
                                raise
                except ImportError:
                    missing_deps.append(req)
                except Exception as e:
                    logger.warning(f"Could not check dependency {req}: {e}")
            
            if missing_deps:
                logger.warning("Missing dependencies: %s", missing_deps)
                response = input("Install missing dependencies? (y/n): ").strip().lower()
                if response == 'y':
                    try:
                        subprocess.check_call([sys.executable, "-m", "pip", "install", *missing_deps])
                        logger.info("Dependencies installed successfully")
                        return True
                    except subprocess.CalledProcessError as e:
                        logger.error(f"Failed to install dependencies: {e}")
                        return False
                return False
            
            logger.info("All dependencies verified")
            return True
            
        except Exception as e:
            logger.error("Failed to verify dependencies: %s", e)
            return False

    def check_qt_conflicts(self) -> bool:
        """Check for Qt binding conflicts and suggest solutions."""
        logger.info("Checking for Qt binding conflicts...")
        
        qt_packages = ['PyQt5', 'PyQt6', 'PySide2', 'PySide6']
        installed_qt = []
        
        for pkg in qt_packages:
            try:
                importlib.import_module(pkg)
                installed_qt.append(pkg)
            except ImportError:
                pass
        
        if len(installed_qt) > 1:
            logger.warning(f"Multiple Qt bindings detected: {installed_qt}")
            logger.warning("This can cause PyInstaller to fail!")
            
            detected_qt = self.detect_qt_version()
            logger.info(f"Application appears to use: {detected_qt}")
            
            other_qt = [pkg for pkg in installed_qt if pkg != detected_qt]
            if other_qt:
                logger.warning(f"Consider uninstalling unused Qt packages: {other_qt}")
                logger.info("Or use --exclude-module options to exclude them")
            
            return False
        elif len(installed_qt) == 1:
            logger.info(f"Single Qt binding detected: {installed_qt[0]}")
            return True
        else:
            logger.error("No Qt bindings found!")
            return False
        
    def verify_directory_structure(self) -> bool:
        """Verify all required directories exist with correct structure."""
        logger.info("Verifying directory structure...")
        missing_items = []

        for dir_path, extensions in self.required_dirs.items():
            dir_full_path = Path(dir_path)
            if not dir_full_path.exists():
                missing_items.append(f"Directory: {dir_path}")
                continue

            # Check for at least one file with required extensions
            has_required_file = False
            for ext in extensions:
                if list(dir_full_path.glob(f"*{ext}")):
                    has_required_file = True
                    break
            
            if not has_required_file:
                missing_items.append(f"No {extensions} files in {dir_path}")

        for file_path in self.critical_files:
            if not Path(file_path).exists():
                missing_items.append(f"Critical file: {file_path}")

        if missing_items:
            logger.warning("Missing required items:")
            for item in missing_items:
                logger.warning("- %s", item)
            return False
        
        logger.info("Directory structure verified")
        return True

    def clean_build_artifacts(self):
        """Clean previous build artifacts."""
        logger.info("Cleaning previous build artifacts...")
        paths_to_clean = [self.build_dir, self.dist_dir]
        
        # Also clean spec files
        for spec_file in glob.glob("*.spec"):
            paths_to_clean.append(Path(spec_file))
            
        for path in paths_to_clean:
            if path.exists():
                if path.is_file():
                    path.unlink()
                    logger.info("Cleaned file %s", path)
                else:
                    shutil.rmtree(path)
                    logger.info("Cleaned directory %s", path)

    def setup_build_environment(self):
        """Setup necessary directories and environment for build."""
        logger.info("Setting up build environment...")
        
        # Create necessary directories
        self.logs_dir.mkdir(exist_ok=True)
        (self.logs_dir / '.gitkeep').touch()
        
        # Create version info
        version_info = {
            'version': '1.0.0',
            'build_date': datetime.now().strftime('%Y.%m.%d'),
            'python_version': sys.version,
        }
        
        with open('version_info.txt', 'w') as f:
            for key, value in version_info.items():
                f.write(f"{key}: {value}\n")
        
        logger.info("Build environment ready")

    def get_data_files(self) -> List[str]:
        """Get list of data files to include in the build."""
        data_files = []
        
        # Add entire resources directory
        if Path('resources').exists():
            data_files.append('resources;resources')
        
        # Add config files
        if Path('config').exists():
            data_files.append('config;config')
        
        # Add utils directory (for license keys)
        if Path('utils').exists():
            data_files.append('utils;utils')
        
        # Add individual critical files
        for file_path in self.critical_files:
            if Path(file_path).exists():
                # For files in subdirectories, preserve the directory structure
                if '/' in file_path:
                    dir_name = str(Path(file_path).parent)
                    data_files.append(f'{file_path};{dir_name}')
                else:
                    data_files.append(f'{file_path};.')
        
        return data_files

    def get_pyinstaller_args(self) -> List[str]:
        """Generate PyInstaller command line arguments."""
        args = [
            self.main_script,
            f'--name={self.app_name}',
            '--clean',
            '--noconfirm',
            '--onefile',
            '--windowed',
            '--noupx',
        ]

        # Add Qt exclusions to prevent conflicts
        for exclusion in self.qt_exclusions:
            args.extend(['--exclude-module', exclusion])

        # Add other standard exclusions
        standard_exclusions = [
            'matplotlib.tests',
            'numpy.tests',
            'scipy.tests',
            'pandas.tests',
            'sklearn.tests',
            'pytest',
            'unittest',
        ]
        
        for exclusion in standard_exclusions:
            args.extend(['--exclude-module', exclusion])

        # Add icon if it exists
        # icon_path = Path('resources/app_icon/wwip_file.ico')
        # if icon_path.exists():
        #     args.extend(['--icon', str(icon_path)])
        # Add icon if it exists
        icon_path = Path('resources/app_icon/WWIP.ico')
        if icon_path.exists():
            args.extend(['--icon', str(icon_path)])

        # Ensure icon files are included
        icon_files = [
            'resources/app_icon/WWIP.ico',
            'resources/app_icon/wwip_file.ico'
        ]
        for icon_file in icon_files:
            if Path(icon_file).exists():
                args.extend(['--add-data', f'{icon_file};resources/app_icon'])


        # Add data files
        data_files = self.get_data_files()
        for data_file in data_files:
            args.extend(['--add-data', data_file])

        # Add hidden imports
        for imp in self.hidden_imports:
            args.extend(['--hidden-import', imp])

        # Add runtime temp directory (fixes some packaging issues)
        args.extend(['--runtime-tmpdir', '.'])

        return args

    def create_installer(self) -> bool:
        """Create NSIS installer after build"""
        try:
            # Check if NSIS is installed
            nsis_paths = [
                r"C:\\Program Files (x86)\\NSIS\\makensis.exe",
                r"C:\\Program Files\\NSIS\\makensis.exe"
            ]
            
            nsis_path = None
            for path in nsis_paths:
                if os.path.exists(path):
                    nsis_path = path
                    break
            
            if not nsis_path:
                logger.warning("NSIS not found in standard locations.")
                logger.warning("Install from: https://nsis.sourceforge.io/Download")
                logger.warning("Or specify custom path in build.py")
                return False

            logger.info(f"Found NSIS at: {nsis_path}")
            
            # Check if installer script exists
            installer_script = Path("installer.nsi")
            if not installer_script.exists():
                logger.warning("installer.nsi not found. Skipping installer creation.")
                return False
                
            # Run NSIS compiler
            logger.info("Creating installer with NSIS...")
            result = subprocess.run([nsis_path, str(installer_script)], 
                                capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("Installer created successfully!")
                return True
            else:
                logger.error(f"NSIS compilation failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error creating installer: {e}")
            return False

    def verify_build_output(self) -> bool:
        """Verify the build was successful."""
        # Check for onefile executable
        exe_path = self.dist_dir / f"{self.app_name}.exe"
        if exe_path.exists():
            logger.info(f"Build successful: {exe_path}")
            return True
        
        # Check for onedir build (fallback)
        dir_path = self.dist_dir / self.app_name
        if dir_path.exists():
            exe_in_dir = dir_path / f"{self.app_name}.exe"
            if exe_in_dir.exists():
                logger.info(f"Build successful: {exe_in_dir}")
                return True
        
        logger.error("Build failed: No executable found")
        return False
    
    def build_executable(self):
        """Build the executable using PyInstaller."""
        data_files = self.get_data_files()
        
        pyinstaller_args = [
            '--name', self.app_name,
            '--onefile',
            '--windowed',
            '--icon', 'resources/app_icon/wwip_file.ico',
        ]
        
        # Add data files
        for data_file in data_files:
            pyinstaller_args.extend(['--add-data', data_file])
        
        # Add hidden imports
        for import_name in self.hidden_imports:
            pyinstaller_args.extend(['--hidden-import', import_name])
        
        # Add main script
        pyinstaller_args.append(self.main_script)
        
        PyInstaller.__main__.run(pyinstaller_args)


    def build(self) -> bool:
        """Execute the build process."""
        logger.info("Starting build process for %s...", self.app_name)

        try:
            # Verify main script exists
            if not Path(self.main_script).exists():
                logger.error(f"Main script {self.main_script} not found!")
                return False

            # Check for Qt conflicts and auto-configure
            qt_version = self.detect_qt_version()
            self.update_hidden_imports_for_qt(qt_version)
            
            # Verify environment
            if not self.verify_python_dependencies():
                logger.error("Failed to verify Python dependencies")
                return False

            if not self.verify_directory_structure():
                response = input("Continue despite missing items? (y/n): ").strip().lower()
                if response != 'y':
                    logger.info("Build cancelled by user")
                    return False

            # Prepare build
            self.clean_build_artifacts()
            self.setup_build_environment()

            # Execute build
            args = self.get_pyinstaller_args()
            logger.info("Running PyInstaller with args: %s", ' '.join(args))
            
            try:
                PyInstaller.__main__.run(args)
            except SystemExit as e:
                if e.code != 0:
                    logger.error(f"PyInstaller failed with exit code: {e.code}")
                    return False

            # Verify build output
            if not self.verify_build_output():
                return False

            logger.info("Build completed successfully!")

            # Create installer
            logger.info("Creating NSIS installer...")
            if self.create_installer():
                logger.info("✓ Installer created: Wind-Data-Insight-Pro-Setup.exe")
            else:
                logger.warning("⚠ Installer creation skipped (NSIS not found or installer.nsi missing)")

            return True

        except KeyboardInterrupt:
            logger.info("Build cancelled by user")
            return False
        except Exception as e:
            logger.error("Build failed with error: %s", e, exc_info=True)
            return False
    
    # Add to build.py or setup script

    def install_file_association():
        """Install file type association during build"""
        from utils.register_filetype import FileTypeRegistrar
        
        registrar = FileTypeRegistrar()
        success = registrar.register(mode="production")
        
        if success:
            print("File association installed")
        else:
            print("Warning: File association failed (may need admin rights)")

def main():
    """Main entry point for the build script."""
    try:
        builder = BuildManager()
        success = builder.build()
        
        if success:
            logger.info("=" * 50)
            logger.info("BUILD COMPLETED SUCCESSFULLY!")
            logger.info("=" * 50)
            print(f"\nExecutable can be found in: {builder.dist_dir}")
        else:
            logger.error("=" * 50)
            logger.error("BUILD FAILED!")
            logger.error("=" * 50)
            print("\nCheck build.log for detailed error information.")
        
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        logger.info("Build interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    main()