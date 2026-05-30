# from PyQt5.QtWidgets import *
# from PyQt5.QtCore import Qt
# from controllers.report.report_controller import ReportController, ReportConfig, ChartConfig

# class ReportConfigDialog(QDialog):
#     """Dialog for configuring report generation."""
    
#     def __init__(self, project_id: int, parent=None):
#         super().__init__(parent)
#         self.project_id = project_id
#         self.controller = ReportController(project_id)
#         self.setWindowTitle("Configure Report")
#         self.setMinimumSize(600, 700)
#         self.setup_ui()
    
#     def setup_ui(self):
#         layout = QVBoxLayout(self)
        
#         # Turbine Selection
#         turbine_group = QGroupBox("Select Turbines")
#         turbine_layout = QVBoxLayout()
        
#         self.turbine_list = QListWidget()
#         self.turbine_list.setSelectionMode(QAbstractItemView.MultiSelection)
#         turbines = self.controller.get_available_turbines()
#         self.turbine_list.addItems(turbines)
#         self.turbine_list.selectAll()
        
#         select_all_btn = QPushButton("Select All")
#         select_all_btn.clicked.connect(self.turbine_list.selectAll)
        
#         turbine_layout.addWidget(self.turbine_list)
#         turbine_layout.addWidget(select_all_btn)
#         turbine_group.setLayout(turbine_layout)
#         layout.addWidget(turbine_group)
        
#         # Chart Selection
#         chart_group = QGroupBox("Select Charts")
#         chart_layout = QVBoxLayout()
        
#         self.chart_widgets = {}
#         charts = self.controller.get_available_charts()
        
#         for chart_id, chart_info in charts.items():
#             chart_widget = self._create_chart_widget(chart_id, chart_info)
#             chart_layout.addWidget(chart_widget)
            
#         chart_group.setLayout(chart_layout)
        
#         scroll = QScrollArea()
#         scroll.setWidget(chart_group)
#         scroll.setWidgetResizable(True)
#         layout.addWidget(scroll)
        
#         # Options
#         options_group = QGroupBox("Report Options")
#         options_layout = QVBoxLayout()
        
#         self.include_metadata = QCheckBox("Include Project Metadata")
#         self.include_metadata.setChecked(True)
#         self.include_summary = QCheckBox("Include Executive Summary")
#         self.include_summary.setChecked(True)
        
#         options_layout.addWidget(self.include_metadata)
#         options_layout.addWidget(self.include_summary)
#         options_group.setLayout(options_layout)
#         layout.addWidget(options_group)
        
#         # Buttons
#         button_layout = QHBoxLayout()
#         generate_btn = QPushButton("Generate Report")
#         cancel_btn = QPushButton("Cancel")
        
#         generate_btn.clicked.connect(self.accept)
#         cancel_btn.clicked.connect(self.reject)
        
#         button_layout.addStretch()
#         button_layout.addWidget(cancel_btn)
#         button_layout.addWidget(generate_btn)
#         layout.addLayout(button_layout)
    
#     def _create_chart_widget(self, chart_id: str, chart_info: dict) -> QWidget:
#         """Create widget for chart configuration."""
#         widget = QWidget()
#         layout = QVBoxLayout(widget)
        
#         # Chart checkbox
#         checkbox = QCheckBox(chart_info['name'])
#         checkbox.setChecked(True)
#         layout.addWidget(checkbox)
        
#         # Parameter selection
#         param_layout = QHBoxLayout()
#         param_layout.addSpacing(20)
#         param_label = QLabel("Parameters:")
#         param_layout.addWidget(param_label)
        
#         param_combo = QListWidget()
#         param_combo.setMaximumHeight(80)
#         param_combo.setSelectionMode(QAbstractItemView.MultiSelection)
#         param_combo.addItems(chart_info['available_params'])
        
#         # Select defaults
#         for i in range(param_combo.count()):
#             item = param_combo.item(i)
#             if item.text() in chart_info['default_params']:
#                 item.setSelected(True)
        
#         param_layout.addWidget(param_combo)
#         layout.addLayout(param_layout)
        
#         self.chart_widgets[chart_id] = {
#             'checkbox': checkbox,
#             'params': param_combo
#         }
        
#         return widget
    
#     def get_config(self) -> ReportConfig:
#         """Get report configuration from dialog."""
#         # Get selected turbines
#         turbine_ids = [item.text() for item in self.turbine_list.selectedItems()]
        
#         # Get selected charts
#         charts = []
#         for chart_id, widgets in self.chart_widgets.items():
#             if widgets['checkbox'].isChecked():
#                 params = [item.text() for item in widgets['params'].selectedItems()]
#                 chart_info = self.controller.get_available_charts()[chart_id]
                
#                 charts.append(ChartConfig(
#                     chart_type=chart_id,
#                     title=chart_info['name'],
#                     parameters=params,
#                     metrics=[],
#                     enabled=True
#                 ))
        
#         return ReportConfig(
#             project_id=self.project_id,
#             turbine_ids=turbine_ids,
#             charts=charts,
#             include_metadata=self.include_metadata.isChecked(),
#             include_summary=self.include_summary.isChecked()
#         )

from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
from controllers.database.database_manager import DatabaseManager

class ReportConfigDialog(QDialog):
    def __init__(self, project_id: int, parent=None):
        super().__init__(parent)
        self.project_id = project_id
        self.db = DatabaseManager()
        self.setWindowTitle("Select Turbines")
        self.setMinimumSize(400, 300)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        label = QLabel("Select turbines for report:")
        layout.addWidget(label)
        
        self.turbine_list = QListWidget()
        self.turbine_list.setSelectionMode(QAbstractItemView.MultiSelection)
        turbines = self.db.get_turbines(self.project_id)
        self.turbine_list.addItems(turbines)
        self.turbine_list.selectAll()
        layout.addWidget(self.turbine_list)
        
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("Generate")
        cancel_btn = QPushButton("Cancel")
        ok_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(ok_btn)
        layout.addLayout(btn_layout)
    
    def get_config(self):
        class Config:
            def __init__(self, turbines):
                self.turbine_ids = turbines
        
        return Config([item.text() for item in self.turbine_list.selectedItems()])
