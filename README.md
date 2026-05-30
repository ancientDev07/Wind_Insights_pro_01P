# Wind Data Insight Pro (WWIP)

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-green.svg)
![License](https://img.shields.io/badge/license-EULA-red.svg)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)

A professional desktop application for comprehensive wind turbine data analysis, visualization, and reporting. Wind Data Insight Pro enables wind farm operators and engineers to monitor performance, optimize operations, and generate detailed analytical reports.

## 🌬️ Overview

Wind Data Insight Pro (WWIP) is a robust, feature-rich desktop application developed for wind farm data management and analysis. It combines high-performance data processing with intuitive visualization tools to help professionals extract actionable insights from complex wind turbine datasets.

### Key Capabilities
- **Project-Based Data Management** - Organize and manage multiple wind farm projects with centralized database storage
- **High-Performance Data Backend** - SQLite database with Write-Ahead Logging (WAL) for fast, concurrent operations
- **High-Speed Data Import** - Process CSV and Excel files with automated validation and bulk insertion
- **Interactive Visualizations** - Dashboards, turbine maps, time series plots, and ranking charts
- **Advanced Analytics** - Statistical analysis and Digital Twin Performance Simulator
- **Professional Report Generation** - Customizable multi-page PDF reports with plots and data tables
- **Theme Support** - Dark/Light theme options with customizable UI
- **Multi-Language Interface** - Configurable language settings
- **Extensible Architecture** - Plugin system for custom features

## 🚀 Quick Start

### System Requirements

**Minimum:**
- Windows 10, macOS 10.14+, or Linux (Ubuntu 18.04+)
- Intel Core i3 processor (2 GHz+)
- 4 GB RAM
- 500 MB free disk space
- 1280x720 display resolution

**Recommended:**
- Windows 11, macOS 12+, or Linux (Ubuntu 20.04+)
- Intel Core i5+ processor (3 GHz+)
- 8 GB+ RAM
- 1 GB free disk space
- 1920x1080+ display resolution

### Installation

#### Using the Installer (Recommended)
1. Download `Wind-Data-Insight-Pro-Setup.exe`
2. Run the installer and follow the setup wizard
3. Complete installation and launch the application
4. Accept the End-User License Agreement on first run

#### From Source
```bash
# Clone the repository
git clone https://github.com/your-repo/Wind-Data-Insight-Pro.git
cd Wind-Data-Insight-Pro

# Install dependencies
pip install -r requirements.txt

# Run the application
python WWIP_APP.py
```

### First Steps
1. Launch Wind Data Insight Pro
2. Create a new project or open an existing one
3. Import wind turbine data from CSV/Excel files
4. Explore the dashboard and visualizations
5. Generate reports as needed

## 📁 Project Structure

```
Wind-Data-Insight-Pro/
├── WWIP_APP.py              # Main application entry point
├── main_app.py              # Core application logic
├── build.py                 # Build configuration
├── requirements.txt         # Python dependencies
├── USER_MANUAL.md           # Comprehensive user guide
│
├── config/                  # Configuration files
│   ├── config.py
│   ├── config.json
│   ├── config.yaml
│   └── iec_validation_rules.json
│
├── controllers/             # Application logic and event handlers
│   ├── central_set_datamanger.py
│   ├── file_menu_controller.py
│   ├── file_handler.py
│   ├── turbine_map.py
│   └── data_controller/
│
├── views/                   # UI components and windows
│   ├── dashboard/
│   ├── components/
│   ├── dialogs/
│   ├── farm_analysis/
│   ├── map/
│   ├── ranking/
│   ├── time_series/
│   └── ai_insights/
│
├── mods/                    # Core modules and utilities
│   ├── ai_engine.py
│   ├── scada_utils.py
│   └── schema_detector.py
│
├── utils/                   # Helper utilities
│   ├── logger.py
│   ├── async_db_worker.py
│   ├── plot_helpers.py
│   ├── numeric_utils.py
│   └── theme_manager.py
│
├── chat/                    # AI and ML components
│   ├── anomaly_model.py
│   ├── power_model.py
│   └── preprocessor.py
│
├── resources/              # Icons, assets, and themes
│   ├── icons/
│   ├── images/
│   ├── app_icon/
│   └── logos/
│
├── tests/                  # Unit and integration tests
│   ├── test_database.py
│   ├── test_ui_components.py
│   ├── test_project_controller.py
│   └── conftest.py
│
├── Docs/                   # Documentation
│   ├── Database_structure.md
│   └── ML_Plan_01.md
│
└── exports/               # Generated reports and exports
```

## 📦 Dependencies

### Core UI Framework
- **PyQt5** - Desktop application framework
- **PyQtChart** - Charting components
- **PyQtWebEngine** - Web content integration

### Data Processing
- **pandas** - Data manipulation and analysis
- **numpy** - Numerical computing
- **scipy** - Scientific computing
- **scikit-learn** - Machine learning

### Visualization
- **matplotlib** - Static plots and visualizations
- **seaborn** - Statistical data visualization
- **pyqtgraph** - Scientific graphics library
- **windrose** - Wind rose diagram generation
- **folium** - Interactive maps

### Database
- **SQLAlchemy** - ORM and database abstraction
- **alembic** - Database migration tool

### Utilities
- **openpyxl** - Excel file handling
- **xlsxwriter** - Excel file creation
- **Pillow** - Image processing
- **python-dotenv** - Environment variable management
- **qdarkstyle** - Dark theme styling

### Development
- **pytest** - Testing framework
- **black** - Code formatting
- **pylint** - Code quality analysis
- **PyInstaller** - Application packaging

## 🛠️ Development

### Setting Up the Development Environment

```bash
# Clone the repository
git clone https://github.com/your-repo/Wind-Data-Insight-Pro.git
cd Wind-Data-Insight-Pro

# Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python WWIP_APP.py
```

### Running Tests
```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_database.py

# Run with verbose output
pytest tests/ -v
```

### Code Quality
```bash
# Format code with black
black . --line-length 100

# Check code quality
pylint mods/ controllers/ views/ utils/
```

### Building the Application
```bash
# Build standalone executable
python build.py
```

## 📊 Key Features Explained

### Project Management
- Create and manage multiple wind farm projects
- Store project metadata (name, location, capacity, etc.)
- Quick access to recent projects
- Export and backup project data

### Data Import and Processing
- Support for CSV and Excel formats
- Automatic data validation and error handling
- Bulk data insertion with progress tracking
- Column mapping and schema detection
- Support for various data types and units

### Visualization Tools
- **Dashboard** - Overview of key metrics and trends
- **Turbine Map** - Geographic visualization of turbines
- **Time Series** - Historical data plots and trends
- **Ranking Charts** - Performance comparison across turbines
- **Wind Rose** - Wind direction and speed distribution

### Analysis Features
- Statistical analysis and correlation studies
- Anomaly detection using ML models
- Power curve analysis
- Performance benchmarking
- Digital Twin simulation

### Report Generation
- Customizable PDF reports
- Multi-page layout with title page and TOC
- Dynamic content selection
- Professional formatting and branding
- Scheduled report generation

## 📖 Documentation

- **[User Manual](USER_MANUAL.md)** - Comprehensive guide for end-users
- **[Database Structure](Docs/Database_structure.md)** - Database schema and design
- **[Configuration Guide](Docs/sdi_implemnt.md)** - Application configuration
- **[Developer Notes](Docs/DEBUGGING%20&%20LEARNING%20NOTES.md)** - Technical implementation details

## 🔒 License

Wind Data Insight Pro is provided under an End-User License Agreement (EULA). See [LICENSE](LICENSE) for full terms and conditions.

### Key License Terms
- **Permitted Uses**: Commercial wind data analysis, multiple computer installation
- **Restrictions**: No distribution, sublicensing, or reverse engineering
- **Warranty**: Provided "AS IS" without warranty
- **Liability**: Not liable for any damages

## 🤝 Contributing

We welcome contributions to improve Wind Data Insight Pro. To contribute:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines
- Follow PEP 8 style guide
- Use black for code formatting
- Add tests for new features
- Update documentation as needed
- Ensure all tests pass before submitting PR

## 🐛 Reporting Issues

Found a bug or have a feature request? Please create an issue in the GitHub repository with:
- Clear description of the problem/request
- Steps to reproduce (for bugs)
- Expected vs. actual behavior
- System information (OS, Python version, etc.)
- Screenshots or logs if applicable

## 📞 Support and Contact

For support, documentation, and additional resources:
- **User Manual**: See [USER_MANUAL.md](USER_MANUAL.md)
- **Issue Tracker**: GitHub Issues
- **Email Support**: [Support contact information]
- **Documentation**: [Docs/](Docs/) directory

## 🔄 Version History

**Version 1.0.0** (May 20, 2026)
- Initial public release
- Core features: project management, data import, visualization
- Advanced analytics and report generation
- Multi-platform support (Windows, macOS, Linux)

## ✨ Acknowledgments

Wind Data Insight Pro was developed by Engineer with contributions from:
- Wind energy industry experts
- Data visualization specialists
- Software development team

## 📝 Citation

If you use Wind Data Insight Pro in your research or analysis, please cite:

```
Wind Data Insight Pro v1.0.0. (2026). 
```

---

**Made with ❤️ for the wind energy industry**

For the latest updates and releases, visit the [GitHub repository](https://github.com/your-repo/Wind-Data-Insight-Pro)
