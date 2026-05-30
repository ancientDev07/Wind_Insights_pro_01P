import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import (
    FigureCanvasQTAgg as FigureCanvas,
    NavigationToolbar2QT as NavigationToolbar,
)
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from models.ai_engine import WindAIEngine
from utils.collapsible_prop import CollapsibleSection
import models.scada_utils as su

class AIWorker(QThread):
    finished = pyqtSignal(list, object)
    error = pyqtSignal(str)

    def __init__(self, df, column_cache, turbine_name):
        super().__init__()
        self.df = df
        self.column_cache = column_cache
        self.turbine_name = turbine_name

    def run(self):
        try:
            engine = WindAIEngine()
            insights = engine.generate_insights(self.df, self.column_cache, self.turbine_name)
            anomalies = engine.detect_anomalies(self.df)
            self.finished.emit(insights, anomalies)
        except Exception as e:
            self.error.emit(str(e))


class AIInsightsWindow(QMainWindow):
    def __init__(self, data: pd.DataFrame, turbine_name: str = "", parent=None, project_id=None):
        super().__init__(parent)
        self.data = data
        self.turbine_name = turbine_name
        self.project_id = project_id
        self.anomaly_df = pd.DataFrame()
        self.engine = WindAIEngine()
        self.column_cache = {}
        self._workers = []

        self.setWindowTitle(f"AI Insights — {turbine_name}")
        self.setGeometry(150, 150, 1400, 850)
        self.setWindowFlags(Qt.Window)
        self.setAttribute(Qt.WA_DeleteOnClose)

        if not self.data.empty:
            self._build_column_cache()

        self._apply_styles()
        self._init_ui()
        self._setup_docks()

        QTimer.singleShot(200, self._run_analysis)

    # ── Column Cache ─────────────────────────────────────────────────────────

    def _build_column_cache(self):
        for param in ["wind_speed", "power", "rotor_speed", "timestamp",
                      "nacelle_direction", "ambient_temp", "generator_speed"]:
            matched = su.find_matching_columns(self.data, param)
            self.column_cache[param] = matched[0] if matched else None

    # ── Styles ───────────────────────────────────────────────────────────────

    def _apply_styles(self):
        self.setStyleSheet("""
            QMainWindow { background-color: #2C3E50; }
            QWidget { background-color: #2C3E50; color: #ECF0F1; }
            QGroupBox {
                font-weight: bold; border: 2px solid #5D6D7E;
                border-radius: 6px; margin-top: 12px; padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin; left: 10px; padding: 0 6px;
                background-color: #3498DB; color: white; border-radius: 3px;
            }
            QPushButton {
                background-color: #3498DB; color: white; border: none;
                padding: 6px 12px; border-radius: 4px; font-size: 11px;
            }
            QPushButton:hover { background-color: #2980B9; }
            QTextEdit {
                background-color: #34495E; color: #ECF0F1;
                border: 1px solid #5D6D7E; border-radius: 4px; font-size: 12px;
            }
            QTableWidget {
                background-color: #34495E; color: #ECF0F1;
                gridline-color: #5D6D7E; font-size: 11px;
            }
            QHeaderView::section {
                background-color: #2C3E50; color: #ECF0F1;
                font-weight: bold; padding: 5px; border: 1px solid #5D6D7E;
            }
            QTableWidget::item:alternate { background-color: #2C3E50; }
            QScrollArea { border: none; }
            QComboBox {
                background-color: #34495E; color: #ECF0F1;
                border: 1px solid #5D6D7E; padding: 4px; border-radius: 3px;
            }
            QCheckBox { color: #ECF0F1; font-size: 11px; padding: 3px; }
        """)

    # ── Main UI ──────────────────────────────────────────────────────────────

    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        sidebar = self._build_sidebar()
        sidebar.setMaximumWidth(300)
        layout.addWidget(sidebar, stretch=25)
        layout.addWidget(self._build_center(), stretch=75)

    def _build_sidebar(self):
        sidebar = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        content = QWidget()
        vbox = QVBoxLayout(content)
        vbox.setSpacing(8)
        vbox.setContentsMargins(6, 6, 6, 6)
        vbox.addWidget(self._section_analysis_options())
        vbox.addWidget(self._section_plot_options())
        vbox.addWidget(self._section_actions())
        vbox.addStretch()

        scroll.setWidget(content)
        outer = QVBoxLayout(sidebar)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)
        return sidebar

    def _section_analysis_options(self):
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(6)

        self.chk_anomaly = QCheckBox("Anomaly Detection")
        self.chk_anomaly.setChecked(True)
        self.chk_performance = QCheckBox("Performance Score")
        self.chk_performance.setChecked(True)
        self.chk_availability = QCheckBox("Availability & PLF")
        self.chk_availability.setChecked(True)
        self.chk_trend = QCheckBox("Wind-Power Trend")
        self.chk_trend.setChecked(True)

        lbl = QLabel("Anomaly Sensitivity:")
        lbl.setStyleSheet("font-size: 11px;")
        self.sensitivity_combo = QComboBox()
        self.sensitivity_combo.addItems(["Low (2%)", "Medium (5%)", "High (10%)"])
        self.sensitivity_combo.setCurrentIndex(1)

        for w in [self.chk_anomaly, self.chk_performance,
                  self.chk_availability, self.chk_trend, lbl, self.sensitivity_combo]:
            layout.addWidget(w)

        return CollapsibleSection("Analysis Options", content, expanded=True)

    def _section_plot_options(self):
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(6)

        lbl = QLabel("Plot Type:")
        lbl.setStyleSheet("font-size: 11px;")
        self.plot_type_combo = QComboBox()
        self.plot_type_combo.addItems([
            "Anomaly Scatter",
            "Power vs Wind Speed",
            "Performance Score Gauge",
            "Rotor Speed Distribution",
            "Availability Timeline",
        ])
        self.plot_type_combo.currentIndexChanged.connect(self._update_plot)

        self.chk_show_anomalies_on_plot = QCheckBox("Highlight Anomalies")
        self.chk_show_anomalies_on_plot.setChecked(True)
        self.chk_show_anomalies_on_plot.stateChanged.connect(self._update_plot)

        layout.addWidget(lbl)
        layout.addWidget(self.plot_type_combo)
        layout.addWidget(self.chk_show_anomalies_on_plot)

        return CollapsibleSection("Plot Options", content, expanded=True)

    def _section_actions(self):
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(6)

        btn_run = QPushButton("🔄 Re-run Analysis")
        btn_run.clicked.connect(self._run_analysis)

        btn_export_anomalies = QPushButton("💾 Export Anomalies (CSV)")
        btn_export_anomalies.clicked.connect(self._export_anomalies)

        btn_export_plot = QPushButton("🖼 Export Plot")
        btn_export_plot.clicked.connect(self._export_plot)

        layout.addWidget(btn_run)
        layout.addWidget(btn_export_anomalies)
        layout.addWidget(btn_export_plot)

        return CollapsibleSection("Actions", content, expanded=True)

    def _build_center(self):
        center = QWidget()
        layout = QVBoxLayout(center)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        self.status_label = QLabel("⏳ Initializing...")
        self.status_label.setStyleSheet(
            "background-color: #34495E; padding: 6px; border-radius: 3px; font-size: 12px;"
        )
        layout.addWidget(self.status_label)

        self.figure = plt.Figure(figsize=(12, 7), facecolor="#34495E")
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setStyleSheet("background-color: #34495E;")
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.toolbar.setStyleSheet("background-color: #34495E; color: #ECF0F1;")

        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        return center

    # ── Docks ────────────────────────────────────────────────────────────────

    def _setup_docks(self):
        # Insights text
        self.insights_dock = QDockWidget("AI Insights", self)
        self.insights_dock.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable)
        self.insights_text = QTextEdit()
        self.insights_text.setReadOnly(True)
        self.insights_text.setPlaceholderText("Analysis results will appear here...")
        self.insights_dock.setWidget(self.insights_text)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.insights_dock)

        # Anomaly table
        self.anomaly_dock = QDockWidget("Anomaly Records", self)
        self.anomaly_dock.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable)
        self.anomaly_table = QTableWidget()
        self.anomaly_table.setAlternatingRowColors(True)
        self.anomaly_dock.setWidget(self.anomaly_table)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.anomaly_dock)

        # Stats table
        self.stats_dock = QDockWidget("Statistics", self)
        self.stats_dock.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable)
        self.stats_table = QTableWidget()
        self.stats_table.setColumnCount(2)
        self.stats_table.setHorizontalHeaderLabels(["Metric", "Value"])
        self.stats_table.horizontalHeader().setStretchLastSection(True)
        self.stats_table.setAlternatingRowColors(True)
        self.stats_dock.setWidget(self.stats_table)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.stats_dock)

        self.tabifyDockWidget(self.insights_dock, self.anomaly_dock)
        self.tabifyDockWidget(self.anomaly_dock, self.stats_dock)
        self.insights_dock.raise_()
        self.resizeDocks([self.insights_dock], [220], Qt.Vertical)

    # ── Analysis ─────────────────────────────────────────────────────────────

    def _get_contamination(self):
        return {"Low (2%)": 0.02, "Medium (5%)": 0.05, "High (10%)": 0.10}.get(
            self.sensitivity_combo.currentText(), 0.05
        )

    def _run_analysis(self):
        if self.data is None or self.data.empty:
            self.status_label.setText("❌ No data loaded")
            return
        self.status_label.setText("⏳ Running AI analysis...")
        self.insights_text.setText("Analyzing...")

        worker = AIWorker(self.data, self.column_cache, self.turbine_name)
        worker.finished.connect(self._on_analysis_done)
        worker.error.connect(lambda e: self.status_label.setText(f"❌ Error: {e}"))
        self._workers.append(worker)
        worker.start()

    def _on_analysis_done(self, insights: list, anomaly_df):
        self.anomaly_df = anomaly_df
        self.insights_text.clear()
        for line in insights:
            self.insights_text.append(line)
        self._populate_anomaly_table(anomaly_df)
        self._populate_stats_table()
        self._update_plot()
        self.status_label.setText(
            f"✅ Analysis complete — {len(anomaly_df)} anomalies in {len(self.data)} records"
        )

    # ── Tables ───────────────────────────────────────────────────────────────

    def _populate_anomaly_table(self, df: pd.DataFrame):
        if df.empty:
            self.anomaly_table.setRowCount(0)
            return
        cols = list(df.columns)
        self.anomaly_table.setColumnCount(len(cols))
        self.anomaly_table.setHorizontalHeaderLabels(cols)
        limit = min(len(df), 500)
        self.anomaly_table.setRowCount(limit)
        for row in range(limit):
            for col, c in enumerate(cols):
                self.anomaly_table.setItem(row, col, QTableWidgetItem(str(df.iloc[row][c])))
        self.anomaly_table.resizeColumnsToContents()

    def _populate_stats_table(self):
        pw_col = self.column_cache.get("power")
        ws_col = self.column_cache.get("wind_speed")
        stats = []

        if pw_col and pw_col in self.data.columns:
            pw = pd.to_numeric(self.data[pw_col], errors="coerce").dropna()
            stats += [
                ("Mean Power (kW)", f"{pw.mean():.2f}"),
                ("Max Power (kW)", f"{pw.max():.2f}"),
                ("PLF (%)", f"{self.engine.plf(self.data, pw_col):.2f}"),
                ("Availability (%)", f"{self.engine.availability(self.data, pw_col):.2f}"),
            ]
        if ws_col and ws_col in self.data.columns:
            ws = pd.to_numeric(self.data[ws_col], errors="coerce").dropna()
            stats += [
                ("Mean Wind Speed (m/s)", f"{ws.mean():.2f}"),
                ("Max Wind Speed (m/s)", f"{ws.max():.2f}"),
            ]
        if pw_col and ws_col:
            stats.append(("Performance Score", f"{self.engine.performance_score(self.data, pw_col, ws_col):.1f}/100"))

        stats.append(("Anomalies Detected", f"{len(self.anomaly_df)} / {len(self.data)}"))

        self.stats_table.setRowCount(len(stats))
        for i, (k, v) in enumerate(stats):
            self.stats_table.setItem(i, 0, QTableWidgetItem(k))
            self.stats_table.setItem(i, 1, QTableWidgetItem(v))
        self.stats_table.resizeColumnsToContents()

    # ── Plots ────────────────────────────────────────────────────────────────

    def _update_plot(self):
        if self.data is None or self.data.empty:
            return
        self.figure.clear()
        plot_type = self.plot_type_combo.currentText()
        try:
            dispatch = {
                "Anomaly Scatter": self._plot_anomaly_scatter,
                "Power vs Wind Speed": self._plot_power_vs_wind,
                "Performance Score Gauge": self._plot_performance_gauge,
                "Rotor Speed Distribution": self._plot_rotor_distribution,
                "Availability Timeline": self._plot_availability_timeline,
            }
            dispatch.get(plot_type, self._plot_anomaly_scatter)()
        except Exception as e:
            ax = self.figure.add_subplot(111)
            ax.set_facecolor("#34495E")
            ax.text(0.5, 0.5, f"Plot error:\n{e}", ha="center", va="center",
                    color="white", fontsize=11)
        self.canvas.draw_idle()

    def _style_ax(self, ax, title, xlabel, ylabel):
        ax.set_facecolor("#34495E")
        ax.set_title(f"{title} — {self.turbine_name}", color="#ECF0F1", fontweight="bold", fontsize=12)
        ax.set_xlabel(xlabel, color="#ECF0F1", fontsize=11)
        ax.set_ylabel(ylabel, color="#ECF0F1", fontsize=11)
        ax.tick_params(colors="#ECF0F1")
        ax.grid(True, alpha=0.2, color="gray")
        for spine in ax.spines.values():
            spine.set_edgecolor("#5D6D7E")

    def _plot_anomaly_scatter(self):
        ws_col = self.column_cache.get("wind_speed")
        pw_col = self.column_cache.get("power")
        if not ws_col or not pw_col:
            return

        ax = self.figure.add_subplot(111)
        ws = pd.to_numeric(self.data[ws_col], errors="coerce")
        pw = pd.to_numeric(self.data[pw_col], errors="coerce")
        mask = ws.notna() & pw.notna()

        ax.scatter(ws[mask], pw[mask], s=8, alpha=0.4, color="#3498DB", label="Normal")

        if self.chk_show_anomalies_on_plot.isChecked() and not self.anomaly_df.empty:
            if ws_col in self.anomaly_df.columns and pw_col in self.anomaly_df.columns:
                aws = pd.to_numeric(self.anomaly_df[ws_col], errors="coerce")
                apw = pd.to_numeric(self.anomaly_df[pw_col], errors="coerce")
                amask = aws.notna() & apw.notna()
                ax.scatter(aws[amask], apw[amask], s=35, color="#E74C3C",
                           label=f"Anomalies ({amask.sum()})", zorder=5, marker="x", linewidths=1.5)

        self._style_ax(ax, "Anomaly Detection", "Wind Speed (m/s)", "Power (kW)")
        ax.legend(facecolor="#2C3E50", labelcolor="#ECF0F1", fontsize=10)
        self.figure.tight_layout()

    def _plot_power_vs_wind(self):
        ws_col = self.column_cache.get("wind_speed")
        pw_col = self.column_cache.get("power")
        if not ws_col or not pw_col:
            return

        ax = self.figure.add_subplot(111)
        ws = pd.to_numeric(self.data[ws_col], errors="coerce")
        pw = pd.to_numeric(self.data[pw_col], errors="coerce")
        mask = ws.notna() & pw.notna()

        ax.scatter(ws[mask], pw[mask], s=6, alpha=0.3, color="#2ECC71", label="Data")

        # Regression line
        from sklearn.linear_model import LinearRegression
        X = ws[mask].values.reshape(-1, 1)
        y = pw[mask].values
        model = LinearRegression().fit(X, y)
        ws_range = np.linspace(ws[mask].min(), ws[mask].max(), 200)
        r2 = round(model.score(X, y), 3)
        ax.plot(ws_range, model.predict(ws_range.reshape(-1, 1)),
                color="#E74C3C", linewidth=2, label=f"Trend (R²={r2})")

        self._style_ax(ax, "Power vs Wind Speed", "Wind Speed (m/s)", "Power (kW)")
        ax.legend(facecolor="#2C3E50", labelcolor="#ECF0F1", fontsize=10)
        self.figure.tight_layout()

    def _plot_performance_gauge(self):
        pw_col = self.column_cache.get("power")
        ws_col = self.column_cache.get("wind_speed")
        if not pw_col or not ws_col:
            return

        score = self.engine.performance_score(self.data, pw_col, ws_col)
        avail = self.engine.availability(self.data, pw_col)
        plf_val = self.engine.plf(self.data, pw_col)

        ax = self.figure.add_subplot(111)
        ax.set_facecolor("#34495E")

        metrics = ["Performance\nScore", "Availability\n(%)", "PLF (%)"]
        values = [score, avail, plf_val]
        colors = ["#3498DB", "#2ECC71", "#E67E22"]

        bars = ax.bar(metrics, values, color=colors, width=0.45, edgecolor="#2C3E50", linewidth=1.5)
        for bar, val in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1.5,
                    f"{val:.1f}", ha="center", va="bottom",
                    color="#ECF0F1", fontweight="bold", fontsize=13)

        ax.set_ylim(0, 115)
        ax.axhline(100, color="white", linestyle="--", alpha=0.3, linewidth=1)
        self._style_ax(ax, "Performance Metrics", "", "Value (%)")
        self.figure.tight_layout()

    def _plot_rotor_distribution(self):
        rs_col = self.column_cache.get("rotor_speed")
        if not rs_col or rs_col not in self.data.columns:
            ax = self.figure.add_subplot(111)
            ax.set_facecolor("#34495E")
            ax.text(0.5, 0.5, "No rotor speed data available", ha="center", va="center",
                    color="#ECF0F1", fontsize=13)
            return

        ax = self.figure.add_subplot(111)
        rs = pd.to_numeric(self.data[rs_col], errors="coerce").dropna()

        ax.hist(rs, bins=40, color="#9B59B6", edgecolor="#2C3E50", alpha=0.85)

        # Mark anomaly rotor speeds if available
        if self.chk_show_anomalies_on_plot.isChecked() and not self.anomaly_df.empty:
            if rs_col in self.anomaly_df.columns:
                ars = pd.to_numeric(self.anomaly_df[rs_col], errors="coerce").dropna()
                if not ars.empty:
                    ax.hist(ars, bins=40, color="#E74C3C", edgecolor="#2C3E50",
                            alpha=0.7, label=f"Anomalies ({len(ars)})")
                    ax.legend(facecolor="#2C3E50", labelcolor="#ECF0F1", fontsize=10)

        # Mean line
        ax.axvline(rs.mean(), color="#F39C12", linestyle="--", linewidth=1.5,
                   label=f"Mean: {rs.mean():.2f}")
        ax.legend(facecolor="#2C3E50", labelcolor="#ECF0F1", fontsize=10)

        self._style_ax(ax, "Rotor Speed Distribution", "Rotor Speed (RPM)", "Frequency")
        self.figure.tight_layout()

    def _plot_availability_timeline(self):
        ts_col = self.column_cache.get("timestamp")
        pw_col = self.column_cache.get("power")
        if not ts_col or not pw_col:
            ax = self.figure.add_subplot(111)
            ax.set_facecolor("#34495E")
            ax.text(0.5, 0.5, "Timestamp or power column not found",
                    ha="center", va="center", color="#ECF0F1", fontsize=13)
            return

        df = self.data[[ts_col, pw_col]].copy()
        df[ts_col] = pd.to_datetime(df[ts_col], errors="coerce")
        df[pw_col] = pd.to_numeric(df[pw_col], errors="coerce")
        df = df.dropna()
        df = df.sort_values(ts_col)

        # Daily availability
        df["date"] = df[ts_col].dt.date
        daily = df.groupby("date").apply(
            lambda g: (g[pw_col] > 0).sum() / len(g) * 100
        ).reset_index()
        daily.columns = ["date", "availability"]

        ax = self.figure.add_subplot(111)
        ax.fill_between(daily["date"], daily["availability"],
                        alpha=0.4, color="#2ECC71")
        ax.plot(daily["date"], daily["availability"],
                color="#2ECC71", linewidth=1.5)
        ax.axhline(daily["availability"].mean(), color="#F39C12",
                   linestyle="--", linewidth=1.5,
                   label=f"Avg: {daily['availability'].mean():.1f}%")

        # Mark anomaly dates
        if self.chk_show_anomalies_on_plot.isChecked() and not self.anomaly_df.empty:
            if ts_col in self.anomaly_df.columns:
                adf = self.anomaly_df.copy()
                adf[ts_col] = pd.to_datetime(adf[ts_col], errors="coerce")
                adf["date"] = adf[ts_col].dt.date
                anomaly_dates = adf["date"].unique()
                for d in anomaly_dates:
                    ax.axvline(pd.Timestamp(d), color="#E74C3C", alpha=0.3, linewidth=1)

        ax.set_ylim(0, 110)
        ax.legend(facecolor="#2C3E50", labelcolor="#ECF0F1", fontsize=10)
        self._style_ax(ax, "Daily Availability Timeline", "Date", "Availability (%)")
        self.figure.autofmt_xdate()
        self.figure.tight_layout()

    # ── Export ───────────────────────────────────────────────────────────────

    def _export_anomalies(self):
        if self.anomaly_df.empty:
            QMessageBox.information(self, "No Anomalies", "No anomalies detected to export.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Export Anomalies", "", "CSV Files (*.csv)")
        if path:
            self.anomaly_df.to_csv(path, index=False)
            QMessageBox.information(self, "Exported", f"Anomalies saved to:\n{path}")

    def _export_plot(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export Plot", "",
                                              "PNG Files (*.png);;PDF Files (*.pdf)")
        if path:
            self.figure.savefig(path, bbox_inches="tight", dpi=300, facecolor="#34495E")
            QMessageBox.information(self, "Exported", f"Plot saved to:\n{path}")

    def closeEvent(self, event):
        for w in self._workers:
            if w.isRunning():
                w.quit()
                w.wait()
        event.accept()