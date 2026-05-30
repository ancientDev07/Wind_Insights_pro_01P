# Wind Data Insight Pro

**Wind Data Insight Pro** is a professional wind turbine data analysis platform featuring project management, advanced visualization, statistical analysis, and comprehensive reporting.

## Features

- Project-based data management (create, open, save, autosave)
- FastAPI backend for user/project/resource management
- Advanced PyQt5 GUI with dashboards, control panels, and admin tools
- Interactive visualizations and statistical analysis
- Professional PDF report generation with user-selected plots/tables
- Plugin/library store for extensibility
- Admin dashboard for user/file/request management

## Directory Structure

```
.
├── WWIP_APP.py                # Main application entry point
├── build.py                   # Build and deployment scripts
├── requirements.txt           # Python dependencies
├── config/                    # Configuration files
├── Authentication/            # FastAPI backend
├── controllers/               # Application logic controllers
├── models/                    # Data models and utilities
├── services/                  # Service layer
├── utils/                     # Utility functions
├── views/                     # PyQt5 GUI components
│   ├── components/
│   ├── dialogs/
│   ├── dashboard/
│   ├── hierarchy/
│   ├── library/
│   ├── main/
│   ├── ranking/
│   ├── statistical_components/
│   └── visualization_components/
├── resources/                 # Icons, images, logos, etc.
└── data/, data_imported/      # Data storage
```

## Getting Started

1. **Install dependencies:**
   ```sh
   pip install -r requirements.txt
   ```

2. **Configure application:**
   - Edit `config/config.json` and `config/config.yaml` as needed.

3. **Run the FastAPI backend:**
   ```sh
   cd Authentication
   uvicorn main:app --reload
   ```

4. **Start the PyQt5 application:**
   ```sh
   python WWIP_APP.py
   ```

## Documentation

- See [views/visualization_components/report_gen.py](views/visualization_components/report_gen.py) for report generation logic.
- See [controllers/file_menu_controller.py](controllers/file_menu_controller.py) for project management.
- See [Authentication/main.py](Authentication/main.py) for backend API.

## License

MIT License. See [LICENSE](LICENSE) for details.

---

## Module Connection Map

![Module Map](docs/module_map.png) <!-- (You can export the above Mermaid diagram as an image and place it here) -->

---

## Contributing

Pull requests are welcome. For major changes, please open an issue first.

---

## Contact

For support, use the "Report Issue" feature in the application or contact the development team.