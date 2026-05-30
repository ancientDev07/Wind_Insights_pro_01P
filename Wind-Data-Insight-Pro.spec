# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main_app.py'],
    pathex=[],
    binaries=[],
    datas=[('resources/app_icon/WWIP.ico', 'resources/app_icon'), ('resources/app_icon/wwip_file.ico', 'resources/app_icon'), ('resources', 'resources'), ('config', 'config'), ('utils', 'utils'), ('config/config.json', 'config'), ('config/config.py', 'config'), ('main_app.py', '.'), ('WWIP_APP.py', '.'), ('resources/app_icon/wwip_file.ico', 'resources\\app_icon'), ('resources/images/splash.png', 'resources\\images'), ('utils/valid_license_keys.json', 'utils'), ('LICENSE', '.')],
    hiddenimports=['qdarkstyle', 'pandas', 'numpy', 'scipy', 'sklearn', 'pyqtgraph', 'pandas.io.parsers', 'pandas.io.parsers.readers', 'pandas.io.common', 'pandas.io.formats.style', 'pandas.io.excel._xlsxwriter', 'pandas.io.excel._openpyxl', 'pandas._libs.parsers', 'pandas._libs.tslibs', 'pandas._libs.tslibs.timedeltas', 'pandas._libs.tslibs.timestamps', 'pandas.tseries', 'pandas.tseries.offsets', 'dateutil', 'dateutil.parser', 'matplotlib', 'matplotlib.backends.backend_qt5agg', 'matplotlib.backends.backend_pdf', 'matplotlib.backends.backend_svg', 'matplotlib.figure', 'matplotlib.dates', 'fontTools.ttLib', 'fontTools.subset', 'fontTools.subset.util', 'pkg_resources.py2_warn', 'PyQt5', 'PyQt5.QtCore', 'PyQt5.QtWidgets', 'PyQt5.QtGui', 'matplotlib.backends.backend_qt5agg'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['PyQt6', 'PyQt6.QtCore', 'PyQt6.QtWidgets', 'PyQt6.QtGui', 'PyQt6.QtOpenGL', 'PyQt6.QtNetwork', 'PyQt6.QtPrintSupport', 'PyQt6.QtSvg', 'PyQt6.QtTest', 'PyQt6.QtXml', 'PySide2', 'PySide6', 'tkinter', 'tk', 'jedi', 'IPython', 'matplotlib.tests', 'numpy.tests', 'scipy.tests', 'pandas.tests', 'sklearn.tests', 'pytest', 'unittest'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Wind-Data-Insight-Pro',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir='.',
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['resources\\app_icon\\WWIP.ico'],
)
