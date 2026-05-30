import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from controllers.database.database_manager import DatabaseManager
from views.visualization_components.power_curve_logic import calculate_binned_curve
from utils.collapsible_prop import CollapsibleSection
from utils.plot_helpers import format_axes, apply_grid


class FarmAnalysisWindow(QMainWindow):
    def __init__(self, project_id, parent=None):
        super().__init__(parent)
        self.project_id = project_id
        self.setWindowTitle("Farm-Level Analysis")
        self.setGeometry(100, 100, 1500, 900)
        self.setWindowFlags(Qt.Window)
        self.setAttribute(Qt.WA_DeleteOnClose)

        self.turbine_data = {}      # {wtg_id: DataFrame}
        self.selected_turbines = [] # list of wtg_ids

        self._load_turbine_list()
        self._init_ui()

    # ── Data Loading ──────────────────────────────────────────────────────────

    def _load_turbine_list(self):
        """Load turbine IDs from DB without loading data yet"""
        try:
            db = DatabaseManager()
            self.all_turbines = db.get_turbines(self.project_id)
            db.close()
        except Exception as e:
            self.all_turbines = []
            print(f"Error loading turbines: {e}")

    def _load_selected_turbines(self):
        """Load SCADA data only for checked turbines"""
        selected = [t for t, cb in self.turbine_checkboxes.items() if cb.isChecked()]
        if not selected:
            QMessageBox.warning(self, "No Selection", "Please select at least one turbine.")
            return

        self.turbine_data = {}
        progress = QProgressDialog("Loading turbine data...", "Cancel", 0, len(selected), self)
        progress.setWindowModality(Qt.WindowModal)

        try:
            db = DatabaseManager()
            for i, wtg_id in enumerate(selected):
                progress.setValue(i)
                progress.setLabelText(f"Loading {wtg_id}...")
                if progress.wasCanceled():
                    break
                df = db.get_turbine_data(self.project_id, wtg_id)
                if not df.empty:
                    self.turbine_data[wtg_id] = df
            db.close()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load data: {e}")
        finally:
            progress.setValue(len(selected))

        self.selected_turbines = list(self.turbine_data.keys())
        self._update_status(f"Loaded {len(self.selected_turbines)} turbines")

    # ── UI ────────────────────────────────────────────────────────────────────

    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)

        layout.addWidget(self._create_left_panel(), stretch=25)
        layout.addWidget(self._create_center_panel(), stretch=75)

        self._setup_summary_dock()
        self.statusBar().showMessage("Ready")

    def _create_left_panel(self):
        panel = QWidget()
        panel.setMaximumWidth(320)
        panel.setStyleSheet("background-color: #2C3E50;")

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background-color: #2C3E50; }")

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(8)
        layout.setContentsMargins(5, 5, 5, 5)

        layout.addWidget(self._create_turbine_section())
        layout.addWidget(self._create_filter_section())
        layout.addWidget(self._create_analysis_section())
        layout.addWidget(self._create_actions_section())
        layout.addStretch()

        scroll.setWidget(content)
        pl = QVBoxLayout(panel)
        pl.setContentsMargins(0, 0, 0, 0)
        pl.addWidget(scroll)
        return panel

    def _create_turbine_section(self):
        content = QWidget()
        layout = QVBoxLayout(content)

        controls = QHBoxLayout()
        btn_all = QPushButton("Select All")
        btn_clear = QPushButton("Clear All")
        btn_all.clicked.connect(lambda: [cb.setChecked(True) for cb in self.turbine_checkboxes.values()])
        btn_clear.clicked.connect(lambda: [cb.setChecked(False) for cb in self.turbine_checkboxes.values()])
        controls.addWidget(btn_all)
        controls.addWidget(btn_clear)
        layout.addLayout(controls)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMaximumHeight(280)
        scroll.setStyleSheet("QScrollArea { border: 1px solid #5D6D7E; background-color: #34495E; }")

        scroll_widget = QWidget()
        cb_layout = QVBoxLayout(scroll_widget)
        cb_layout.setSpacing(3)
        cb_layout.setContentsMargins(5, 5, 5, 5)

        self.turbine_checkboxes = {}
        for turbine in self.all_turbines:
            cb = QCheckBox(str(turbine))
            cb.setStyleSheet("color: #ECF0F1; font-size: 11px;")
            self.turbine_checkboxes[turbine] = cb
            cb_layout.addWidget(cb)

        cb_layout.addStretch()
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)

        return CollapsibleSection("Turbine Selection", content, expanded=True)

    def _create_filter_section(self):
        content = QWidget()
        layout = QGridLayout(content)

        self.enable_date_filter = QCheckBox("Enable Date Filter")
        self.enable_date_filter.setChecked(True)
        layout.addWidget(self.enable_date_filter, 0, 0, 1, 2)

        layout.addWidget(QLabel("From:"), 1, 0)
        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDate(QDate.currentDate().addYears(-1))
        layout.addWidget(self.start_date, 1, 1)

        layout.addWidget(QLabel("To:"), 2, 0)
        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDate(QDate.currentDate())
        layout.addWidget(self.end_date, 2, 1)

        for lbl in content.findChildren(QLabel):
            lbl.setStyleSheet("color: #ECF0F1; font-size: 11px;")

        return CollapsibleSection("Date Filter", content, expanded=True)

    def _create_analysis_section(self):
        content = QWidget()
        layout = QVBoxLayout(content)

        layout.addWidget(QLabel("Analysis Type:"))
        self.analysis_combo = QComboBox()
        self.analysis_combo.addItems([
            "Comparative Power Curve",
            "Power Output Comparison",
            "Capacity Factor",
            "Wind Speed Distribution"
        ])
        layout.addWidget(self.analysis_combo)

        self.enable_iec_binning = QCheckBox("Enable IEC Binning (0.5 m/s)")
        self.enable_iec_binning.setChecked(True)
        layout.addWidget(self.enable_iec_binning)

        for lbl in content.findChildren(QLabel):
            lbl.setStyleSheet("color: #ECF0F1; font-size: 11px;")

        return CollapsibleSection("Analysis Settings", content, expanded=True)

    def _create_actions_section(self):
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(6)

        btn_style = """
            QPushButton {
                font-size: 11px; padding: 8px;
                background-color: #3498DB; color: white;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #2980B9; }
        """

        self.btn_load = QPushButton("📂 Load Selected Turbines")
        self.btn_analyse = QPushButton("📊 Run Analysis")
        self.btn_report = QPushButton("📄 Generate Reports")

        self.btn_load.clicked.connect(self._load_selected_turbines)
        self.btn_analyse.clicked.connect(self._run_analysis)
        self.btn_report.clicked.connect(self._generate_reports)

        for btn in [self.btn_load, self.btn_analyse, self.btn_report]:
            btn.setStyleSheet(btn_style)
            layout.addWidget(btn)

        return CollapsibleSection("Actions", content, expanded=True)

    def _create_center_panel(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(5, 5, 5, 5)

        # Tab widget — one tab per turbine + one "All" overview tab
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("QTabWidget { font-size: 11px; }")
        layout.addWidget(self.tab_widget)

        return panel

    def _setup_summary_dock(self):
        self.summary_dock = QDockWidget("Farm Summary", self)
        self.summary_table = QTableWidget()
        self.summary_table.setAlternatingRowColors(True)
        self.summary_dock.setWidget(self.summary_table)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.summary_dock)

    # ── Analysis ──────────────────────────────────────────────────────────────

    def _get_filtered_df(self, df):
        """Apply date filter to a turbine DataFrame"""
        if not self.enable_date_filter.isChecked():
            return df

        import models.scada_utils as su
        ts_cols = su.find_matching_columns(df, 'timestamp')
        if not ts_cols:
            return df

        ts_col = ts_cols[0]
        df[ts_col] = pd.to_datetime(df[ts_col], errors='coerce')
        start = pd.Timestamp(self.start_date.date().toPyDate())
        end = pd.Timestamp(self.end_date.date().toPyDate())
        return df[(df[ts_col] >= start) & (df[ts_col] <= end)]

    def _run_analysis(self):
        if not self.turbine_data:
            QMessageBox.warning(self, "No Data", "Load turbines first.")
            return

        analysis = self.analysis_combo.currentText()
        self.tab_widget.clear()

        # Overview tab — all turbines on one plot
        self._add_overview_tab(analysis)

        # Individual tab per turbine
        for wtg_id, df in self.turbine_data.items():
            self._add_turbine_tab(wtg_id, df, analysis)

        self._update_summary_table()

    def _add_overview_tab(self, analysis):
        """All turbines overlaid on one axis"""
        fig = plt.Figure(figsize=(12, 6))
        canvas = FigureCanvas(fig)
        ax = fig.add_subplot(111)
        colors = plt.cm.tab10(np.linspace(0, 1, len(self.turbine_data)))

        for i, (wtg_id, df) in enumerate(self.turbine_data.items()):
            filtered = self._get_filtered_df(df)
            if filtered.empty:
                continue
            self._plot_on_axis(ax, filtered, wtg_id, analysis, colors[i])

        ax.legend(fontsize=9)
        ax.set_title(f"Farm Overview — {analysis}", fontweight='bold')
        apply_grid(ax)
        fig.tight_layout()

        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.addWidget(NavigationToolbar(canvas, tab))
        layout.addWidget(canvas)
        self.tab_widget.addTab(tab, "🌍 All Turbines")

    def _add_turbine_tab(self, wtg_id, df, analysis):
        """Individual turbine tab"""
        filtered = self._get_filtered_df(df)

        fig = plt.Figure(figsize=(12, 6))
        canvas = FigureCanvas(fig)
        ax = fig.add_subplot(111)

        self._plot_on_axis(ax, filtered, wtg_id, analysis, color='steelblue')
        ax.legend(fontsize=9)
        apply_grid(ax)
        fig.tight_layout()

        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.addWidget(NavigationToolbar(canvas, tab))
        layout.addWidget(canvas)
        self.tab_widget.addTab(tab, str(wtg_id))

    def _plot_on_axis(self, ax, df, wtg_id, analysis, color):
        """Route to correct plot based on analysis type"""
        if analysis == "Comparative Power Curve":
            self._plot_power_curve(ax, df, wtg_id, color)
        elif analysis == "Power Output Comparison":
            self._plot_power_output(ax, df, wtg_id, color)
        elif analysis == "Capacity Factor":
            self._plot_capacity_factor(ax, df, wtg_id, color)
        elif analysis == "Wind Speed Distribution":
            self._plot_wind_distribution(ax, df, wtg_id, color)

    def _plot_power_curve(self, ax, df, wtg_id, color):
        """Reuse calculate_binned_curve from power_curve_logic"""
        bin_stats = calculate_binned_curve(df, self.enable_iec_binning.isChecked())
        if not bin_stats.empty:
            ax.plot(bin_stats['wind_speed'], bin_stats['power_mean'],
                    'o-', color=color, linewidth=2, markersize=4,
                    label=str(wtg_id), alpha=0.85)
        format_axes(ax, "Wind Speed (m/s)", "Power (kW)", "Comparative Power Curve")

    def _plot_power_output(self, ax, df, wtg_id, color):
        import models.scada_utils as su
        power_cols = su.find_matching_columns(df, 'power')
        ts_cols = su.find_matching_columns(df, 'timestamp')
        if not power_cols or not ts_cols:
            return
        ax.plot(pd.to_datetime(df[ts_cols[0]], errors='coerce'),
                pd.to_numeric(df[power_cols[0]], errors='coerce'),
                color=color, linewidth=1, alpha=0.7, label=str(wtg_id))
        format_axes(ax, "Time", "Power (kW)", "Power Output")

    def _plot_capacity_factor(self, ax, df, wtg_id, color):
        import models.scada_utils as su
        power_cols = su.find_matching_columns(df, 'power')
        if not power_cols:
            return
        power = pd.to_numeric(df[power_cols[0]], errors='coerce').dropna()
        rated = power.quantile(0.95)
        cf = (power / rated).clip(0, 1).mean() * 100 if rated > 0 else 0
        ax.bar(str(wtg_id), cf, color=color, alpha=0.85, label=str(wtg_id))
        format_axes(ax, "Turbine", "Capacity Factor (%)", "Capacity Factor Comparison")

    def _plot_wind_distribution(self, ax, df, wtg_id, color):
        import models.scada_utils as su
        ws_cols = su.find_matching_columns(df, 'wind_speed')
        if not ws_cols:
            return
        ws = pd.to_numeric(df[ws_cols[0]], errors='coerce').dropna()
        ax.hist(ws, bins=20, alpha=0.5, color=color, label=str(wtg_id), density=True)
        format_axes(ax, "Wind Speed (m/s)", "Density", "Wind Speed Distribution")

    # ── Summary Table ─────────────────────────────────────────────────────────

    def _update_summary_table(self):
        import models.scada_utils as su

        rows = []
        for wtg_id, df in self.turbine_data.items():
            filtered = self._get_filtered_df(df)
            power_cols = su.find_matching_columns(filtered, 'power')
            ws_cols = su.find_matching_columns(filtered, 'wind_speed')

            if not power_cols or not ws_cols:
                continue

            power = pd.to_numeric(filtered[power_cols[0]], errors='coerce').dropna()
            ws = pd.to_numeric(filtered[ws_cols[0]], errors='coerce').dropna()
            rated = power.quantile(0.95) if not power.empty else 0
            cf = (power / rated).clip(0, 1).mean() * 100 if rated > 0 else 0

            rows.append({
                'Turbine': wtg_id,
                'Records': len(filtered),
                'Mean Power (kW)': f"{power.mean():.1f}" if not power.empty else '-',
                'Max Power (kW)': f"{power.max():.1f}" if not power.empty else '-',
                'Capacity Factor (%)': f"{cf:.1f}",
                'Mean Wind Speed (m/s)': f"{ws.mean():.2f}" if not ws.empty else '-',
            })

        if not rows:
            return

        self.summary_table.setRowCount(len(rows))
        self.summary_table.setColumnCount(len(rows[0]))
        self.summary_table.setHorizontalHeaderLabels(list(rows[0].keys()))

        for i, row in enumerate(rows):
            for j, val in enumerate(row.values()):
                self.summary_table.setItem(i, j, QTableWidgetItem(str(val)))

        self.summary_table.resizeColumnsToContents()

    # ── Report Generation ─────────────────────────────────────────────────────

    def _generate_reports(self):
        if not self.turbine_data:
            QMessageBox.warning(self, "No Data", "Load and analyse turbines first.")
            return

        folder = QFileDialog.getExistingDirectory(self, "Select Report Output Folder")
        if not folder:
            return

        progress = QProgressDialog("Generating reports...", "Cancel", 0, len(self.turbine_data), self)
        progress.setWindowModality(Qt.WindowModal)

        analysis = self.analysis_combo.currentText()

        for i, (wtg_id, df) in enumerate(self.turbine_data.items()):
            progress.setValue(i)
            progress.setLabelText(f"Generating report for {wtg_id}...")
            if progress.wasCanceled():
                break

            filtered = self._get_filtered_df(df)
            self._generate_single_report(wtg_id, filtered, analysis, folder)

        progress.setValue(len(self.turbine_data))
        QMessageBox.information(self, "Done", f"Reports saved to:\n{folder}")

    def _generate_single_report(self, wtg_id, df, analysis, folder):
        """Generate a single PDF report for one turbine"""
        import os
        from matplotlib.backends.backend_pdf import PdfPages

        file_path = os.path.join(folder, f"Report_{wtg_id}.pdf")

        with PdfPages(file_path) as pdf:
            # Page 1 — Power Curve
            fig, ax = plt.subplots(figsize=(10, 6))
            self._plot_power_curve(ax, df, wtg_id, color='steelblue')
            ax.set_title(f"{wtg_id} — Power Curve", fontweight='bold')
            pdf.savefig(fig, bbox_inches='tight')
            plt.close(fig)

            # Page 2 — Power Output
            fig, ax = plt.subplots(figsize=(10, 6))
            self._plot_power_output(ax, df, wtg_id, color='steelblue')
            ax.set_title(f"{wtg_id} — Power Output", fontweight='bold')
            pdf.savefig(fig, bbox_inches='tight')
            plt.close(fig)

            # Page 3 — Summary stats table
            fig, ax = plt.subplots(figsize=(10, 4))
            ax.axis('off')
            import models.scada_utils as su
            power_cols = su.find_matching_columns(df, 'power')
            ws_cols = su.find_matching_columns(df, 'wind_speed')
            if power_cols and ws_cols:
                power = pd.to_numeric(df[power_cols[0]], errors='coerce').dropna()
                ws = pd.to_numeric(df[ws_cols[0]], errors='coerce').dropna()
                rated = power.quantile(0.95) if not power.empty else 0
                cf = (power / rated).clip(0, 1).mean() * 100 if rated > 0 else 0
                table_data = [
                    ['Records', str(len(df))],
                    ['Mean Power (kW)', f"{power.mean():.1f}"],
                    ['Max Power (kW)', f"{power.max():.1f}"],
                    ['Capacity Factor (%)', f"{cf:.1f}"],
                    ['Mean Wind Speed (m/s)', f"{ws.mean():.2f}"],
                ]
                ax.table(cellText=table_data, colLabels=['Metric', 'Value'],
                         loc='center', cellLoc='left')
                ax.set_title(f"{wtg_id} — Summary Statistics", fontweight='bold')
            pdf.savefig(fig, bbox_inches='tight')
            plt.close(fig)

    def _update_status(self, msg):
        self.statusBar().showMessage(msg)