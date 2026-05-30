import requests
import json
import pandas as pd
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from utils.collapsible_prop import CollapsibleSection


OLLAMA_URL = "http://localhost:11435/api/generate"
DEFAULT_MODEL = "gemma4:e4b"


class OllamaWorker(QThread):
    token_received = pyqtSignal(str)
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, model: str, prompt: str):
        super().__init__()
        self.model = model
        self.prompt = prompt
        self._running = True

    def run(self):
        try:
            response = requests.post(
                OLLAMA_URL,
                json={"model": self.model, "prompt": self.prompt, "stream": True},
                stream=True,
                timeout=120,
            )
            response.raise_for_status()
            for line in response.iter_lines():
                if not self._running:
                    break
                if line:
                    data = json.loads(line.decode("utf-8"))
                    token = data.get("response", "")
                    if token:
                        self.token_received.emit(token)
                    if data.get("done", False):
                        break
        except requests.exceptions.ConnectionError:
            self.error.emit(
                "Cannot connect to Ollama.\n\n"
                "Make sure Ollama is running:\n"
                "  ollama serve\n\n"
                "And the model is pulled:\n"
                f"  ollama pull {self.model}"
            )
        except Exception as e:
            self.error.emit(str(e))
        finally:
            self.finished.emit()

    def stop(self):
        self._running = False


class ChatBubble(QFrame):
    """Single chat message bubble."""

    def __init__(self, text: str, is_user: bool, parent=None):
        super().__init__(parent)
        self.is_user = is_user

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)

        label = QTextEdit()
        label.setReadOnly(True)
        label.setPlainText(text)
        label.setFrameShape(QFrame.NoFrame)
        label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        label.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        label.document().setDocumentMargin(8)

        # Auto-resize height to content
        label.document().contentsChanged.connect(
            lambda: label.setFixedHeight(
                int(label.document().size().height()) + 16
            )
        )

        if is_user:
            label.setStyleSheet("""
                QTextEdit {
                    background-color: #2980B9;
                    color: #FFFFFF;
                    border-radius: 10px;
                    font-size: 12px;
                    padding: 4px;
                }
            """)
            layout.addStretch()
            layout.addWidget(label, stretch=80)
        else:
            label.setStyleSheet("""
                QTextEdit {
                    background-color: #34495E;
                    color: #ECF0F1;
                    border-radius: 10px;
                    font-size: 12px;
                    padding: 4px;
                }
            """)
            layout.addWidget(label, stretch=80)
            layout.addStretch()

        self.label = label
        self.setStyleSheet("background: transparent; border: none;")

    def append_text(self, token: str):
        self.label.setPlainText(self.label.toPlainText() + token)
        self.label.setFixedHeight(
            int(self.label.document().size().height()) + 16
        )


class ChatPanel(QMainWindow):
    def __init__(self, data: pd.DataFrame = None, turbine_name: str = "",
                 project_id=None, parent=None):
        super().__init__(parent)
        self.data = data
        self.turbine_name = turbine_name
        self.project_id = project_id
        self._worker = None
        self._current_bubble = None
        self._history = []  # list of {"role": "user"/"assistant", "content": str}

        self.setWindowTitle(f"AI Chat Assistant — {turbine_name}" if turbine_name else "AI Chat Assistant")
        self.setGeometry(200, 200, 1000, 700)
        self.setWindowFlags(Qt.Window)
        self.setAttribute(Qt.WA_DeleteOnClose)

        self._apply_styles()
        self._init_ui()
        self._check_ollama()

    # ── Styles ───────────────────────────────────────────────────────────────

    def _apply_styles(self):
        self.setStyleSheet("""
            QMainWindow { background-color: #2C3E50; }
            QWidget     { background-color: #2C3E50; color: #ECF0F1; }
            QScrollArea { border: none; background-color: #2C3E50; }
            QLineEdit {
                background-color: #34495E; color: #ECF0F1;
                border: 1px solid #5D6D7E; border-radius: 6px;
                padding: 8px; font-size: 13px;
            }
            QLineEdit:focus { border: 1px solid #3498DB; }
            QPushButton {
                background-color: #3498DB; color: white; border: none;
                padding: 8px 16px; border-radius: 6px; font-size: 12px;
            }
            QPushButton:hover   { background-color: #2980B9; }
            QPushButton:disabled { background-color: #5D6D7E; }
            QComboBox {
                background-color: #34495E; color: #ECF0F1;
                border: 1px solid #5D6D7E; padding: 4px; border-radius: 4px;
            }
            QLabel { color: #ECF0F1; }
            QGroupBox {
                border: 1px solid #5D6D7E; border-radius: 6px;
                margin-top: 10px; padding-top: 8px; font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin; left: 10px; padding: 0 6px;
                background-color: #3498DB; color: white; border-radius: 3px;
            }
        """)

    # ── UI ───────────────────────────────────────────────────────────────────

    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Left sidebar
        sidebar = self._build_sidebar()
        sidebar.setFixedWidth(260)
        main_layout.addWidget(sidebar)

        # Right chat area
        main_layout.addWidget(self._build_chat_area())

    def _build_sidebar(self):
        sidebar = QWidget()
        sidebar.setStyleSheet("background-color: #243342; border-right: 1px solid #3D5166;")
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background-color: #243342; border: none;")

        content = QWidget()
        content.setStyleSheet("background-color: #243342;")
        vbox = QVBoxLayout(content)
        vbox.setSpacing(10)
        vbox.setContentsMargins(8, 8, 8, 8)

        vbox.addWidget(self._section_model())
        vbox.addWidget(self._section_context())
        vbox.addWidget(self._section_quick_prompts())
        vbox.addStretch()

        # Status indicator
        self.status_indicator = QLabel("⚪ Checking Ollama...")
        self.status_indicator.setStyleSheet("font-size: 11px; padding: 4px;")
        vbox.addWidget(self.status_indicator)

        scroll.setWidget(content)
        outer = QVBoxLayout(sidebar)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)
        return sidebar

    def _section_model(self):
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(6)

        lbl = QLabel("Model:")
        lbl.setStyleSheet("font-size: 11px;")
        self.model_combo = QComboBox()
        self.model_combo.addItems([
            "gemma4:e4b",
            "gemma4:e4b",
        ])
        self.model_combo.setCurrentText(DEFAULT_MODEL)

        lbl_temp = QLabel("Context Mode:")
        lbl_temp.setStyleSheet("font-size: 11px;")
        self.context_mode = QComboBox()
        self.context_mode.addItems([
            "Wind Data Expert",
            "General Assistant",
            "Data Analyst",
        ])

        layout.addWidget(lbl)
        layout.addWidget(self.model_combo)
        layout.addWidget(lbl_temp)
        layout.addWidget(self.context_mode)

        return CollapsibleSection("Model Settings", content, expanded=True)

    def _section_context(self):
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(6)

        self.chk_include_stats = QCheckBox("Include turbine statistics")
        self.chk_include_stats.setChecked(True)
        self.chk_include_stats.setStyleSheet("font-size: 11px; color: #ECF0F1;")

        self.chk_include_columns = QCheckBox("Include column names")
        self.chk_include_columns.setChecked(True)
        self.chk_include_columns.setStyleSheet("font-size: 11px; color: #ECF0F1;")

        self.chk_include_anomaly = QCheckBox("Include anomaly hint")
        self.chk_include_anomaly.setChecked(False)
        self.chk_include_anomaly.setStyleSheet("font-size: 11px; color: #ECF0F1;")

        btn_clear = QPushButton("🗑 Clear Chat")
        btn_clear.clicked.connect(self._clear_chat)

        layout.addWidget(self.chk_include_stats)
        layout.addWidget(self.chk_include_columns)
        layout.addWidget(self.chk_include_anomaly)
        layout.addWidget(btn_clear)

        return CollapsibleSection("Context Options", content, expanded=True)

    def _section_quick_prompts(self):
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(5)

        prompts = [
            ("📊 Summarize data", "Summarize the wind turbine data and highlight key observations."),
            ("⚠ Find issues", "What potential issues or anomalies do you see in this turbine data?"),
            ("💡 Improve PLF", "How can I improve the Plant Load Factor for this turbine?"),
            ("🌬 Wind analysis", "Analyze the wind speed patterns and their impact on power output."),
            ("🔧 Maintenance tip", "Based on the data, what maintenance actions would you recommend?"),
            ("📈 Performance", "Evaluate the overall performance of this turbine against typical benchmarks."),
        ]

        for label, prompt in prompts:
            btn = QPushButton(label)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #2C3E50; color: #ECF0F1;
                    border: 1px solid #5D6D7E; border-radius: 4px;
                    padding: 6px; font-size: 11px; text-align: left;
                }
                QPushButton:hover { background-color: #3D5166; }
            """)
            btn.clicked.connect(lambda _, p=prompt: self._send_message(p))
            layout.addWidget(btn)

        return CollapsibleSection("Quick Prompts", content, expanded=True)

    def _build_chat_area(self):
        chat_widget = QWidget()
        layout = QVBoxLayout(chat_widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        # Header
        header = QLabel(
            f"🤖 Gemma AI Assistant"
            + (f" — {self.turbine_name}" if self.turbine_name else "")
        )
        header.setStyleSheet(
            "font-size: 14px; font-weight: bold; padding: 6px;"
            "background-color: #243342; border-radius: 6px;"
        )
        layout.addWidget(header)

        # Messages scroll area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("background-color: #2C3E50; border: 1px solid #3D5166; border-radius: 6px;")

        self.messages_widget = QWidget()
        self.messages_widget.setStyleSheet("background-color: #2C3E50;")
        self.messages_layout = QVBoxLayout(self.messages_widget)
        self.messages_layout.setSpacing(6)
        self.messages_layout.setContentsMargins(8, 8, 8, 8)
        self.messages_layout.addStretch()

        self.scroll_area.setWidget(self.messages_widget)
        layout.addWidget(self.scroll_area)

        # Typing indicator
        self.typing_label = QLabel("● Gemma is thinking...")
        self.typing_label.setStyleSheet(
            "color: #3498DB; font-size: 11px; font-style: italic; padding: 2px 8px;"
        )
        self.typing_label.hide()
        layout.addWidget(self.typing_label)

        # Input row
        input_row = QHBoxLayout()
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Ask anything about your wind turbine data...")
        self.input_field.returnPressed.connect(self._on_send)

        self.send_btn = QPushButton("Send ➤")
        self.send_btn.setFixedWidth(90)
        self.send_btn.clicked.connect(self._on_send)

        self.stop_btn = QPushButton("■ Stop")
        self.stop_btn.setFixedWidth(80)
        self.stop_btn.setStyleSheet(
            "background-color: #E74C3C; color: white; border-radius: 6px; padding: 8px;"
        )
        self.stop_btn.clicked.connect(self._stop_generation)
        self.stop_btn.hide()

        input_row.addWidget(self.input_field)
        input_row.addWidget(self.send_btn)
        input_row.addWidget(self.stop_btn)
        layout.addLayout(input_row)

        return chat_widget

    # ── Ollama Check ─────────────────────────────────────────────────────────

    def _check_ollama(self):
        try:
            r = requests.get(OLLAMA_URL, timeout=3)
            if r.status_code == 200:
                mods = [m["name"] for m in r.json().get("mods", [])]
                self.status_indicator.setText("🟢 Ollama connected")
                self.status_indicator.setStyleSheet("color: #2ECC71; font-size: 11px; padding: 4px;")
                # Add any locally available mods to combo
                for m in mods:
                    if self.model_combo.findText(m) == -1:
                        self.model_combo.addItem(m)
                # Show welcome message
                self._add_assistant_bubble(
                    "👋 Hello! I'm your Wind Data AI Assistant powered by Gemma.\n\n"
                    "I have access to your turbine data context. Ask me anything about:\n"
                    "• Wind speed & power analysis\n"
                    "• Performance issues & anomalies\n"
                    "• Maintenance recommendations\n"
                    "• Data interpretation\n\n"
                    "Use the Quick Prompts on the left to get started!"
                )
            else:
                self._ollama_offline()
        except Exception:
            self._ollama_offline()

    def _ollama_offline(self):
        self.status_indicator.setText("🔴 Ollama offline")
        self.status_indicator.setStyleSheet("color: #E74C3C; font-size: 11px; padding: 4px;")
        self._add_assistant_bubble(
            "⚠️ Ollama is not running.\n\n"
            "To use the AI chat:\n"
            "1. Install Ollama: https://ollama.com\n"
            "2. Run in terminal:  ollama serve\n"
            f"3. Pull the model:  ollama pull {DEFAULT_MODEL}\n\n"
            "Then reopen this chat panel."
        )
        self.send_btn.setEnabled(False)
        self.input_field.setEnabled(False)

    # ── Context Builder ───────────────────────────────────────────────────────

    def _build_system_context(self) -> str:
        mode = self.context_mode.currentText()

        if mode == "Wind Data Expert":
            system = (
                "You are an expert wind energy engineer and data analyst. "
                "You specialize in SCADA data analysis, turbine performance, "
                "IEC standards, and wind farm operations. "
                "Give concise, technical, and actionable answers."
            )
        elif mode == "Data Analyst":
            system = (
                "You are a data analyst specializing in time-series energy data. "
                "Focus on statistical insights, trends, and data quality issues."
            )
        else:
            system = "You are a helpful AI assistant."

        context_parts = [system]

        if self.data is not None and not self.data.empty:
            if self.turbine_name:
                context_parts.append(f"Current turbine: {self.turbine_name}")

            if self.chk_include_columns.isChecked():
                cols = list(self.data.columns)
                context_parts.append(f"Available data columns: {', '.join(cols)}")

            if self.chk_include_stats.isChecked():
                try:
                    import mods.scada_utils as su
                    pw_cols = su.find_matching_columns(self.data, "power")
                    ws_cols = su.find_matching_columns(self.data, "wind_speed")
                    stats_lines = [f"Dataset: {len(self.data)} records"]

                    if pw_cols:
                        pw = pd.to_numeric(self.data[pw_cols[0]], errors="coerce").dropna()
                        stats_lines.append(
                            f"Power — Mean: {pw.mean():.1f} kW, Max: {pw.max():.1f} kW, "
                            f"Negative readings: {(pw < 0).sum()}"
                        )
                    if ws_cols:
                        ws = pd.to_numeric(self.data[ws_cols[0]], errors="coerce").dropna()
                        stats_lines.append(
                            f"Wind Speed — Mean: {ws.mean():.2f} m/s, Max: {ws.max():.2f} m/s"
                        )
                    context_parts.append("\n".join(stats_lines))
                except Exception:
                    pass

            if self.chk_include_anomaly.isChecked():
                try:
                    from mods.ai_engine import WindAIEngine
                    import mods.scada_utils as su
                    cache = {}
                    for param in ["wind_speed", "power", "rotor_speed"]:
                        matched = su.find_matching_columns(self.data, param)
                        cache[param] = matched[0] if matched else None
                    engine = WindAIEngine()
                    anomalies = engine.detect_anomalies(self.data)
                    pct = round(len(anomalies) / len(self.data) * 100, 1)
                    context_parts.append(
                        f"Anomaly detection: {len(anomalies)} anomalous records ({pct}%)"
                    )
                except Exception:
                    pass

        return "\n\n".join(context_parts)

    def _build_full_prompt(self, user_message: str) -> str:
        system_ctx = self._build_system_context()

        # Include last 6 turns of history for context
        history_text = ""
        for turn in self._history[-6:]:
            role = "User" if turn["role"] == "user" else "Assistant"
            history_text += f"{role}: {turn['content']}\n"

        return (
            f"{system_ctx}\n\n"
            f"{history_text}"
            f"User: {user_message}\n"
            f"Assistant:"
        )

    # ── Send / Receive ────────────────────────────────────────────────────────

    def _on_send(self):
        text = self.input_field.text().strip()
        if not text:
            return
        self.input_field.clear()
        self._send_message(text)

    def _send_message(self, text: str):
        # Add user bubble
        self._add_user_bubble(text)
        self._history.append({"role": "user", "content": text})

        # Disable input while generating
        self.send_btn.setEnabled(False)
        self.input_field.setEnabled(False)
        self.stop_btn.show()
        self.typing_label.show()

        # Create assistant bubble (streaming target)
        self._current_bubble = self._add_assistant_bubble("")

        # Start worker
        model = self.model_combo.currentText()
        prompt = self._build_full_prompt(text)

        self._worker = OllamaWorker(model, prompt)
        self._worker.token_received.connect(self._on_token)
        self._worker.finished.connect(self._on_generation_done)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _on_token(self, token: str):
        if self._current_bubble:
            self._current_bubble.append_text(token)
            # Auto-scroll to bottom
            QTimer.singleShot(10, self._scroll_to_bottom)

    def _on_generation_done(self):
        # Save assistant response to history
        if self._current_bubble:
            content = self._current_bubble.label.toPlainText()
            self._history.append({"role": "assistant", "content": content})

        self.send_btn.setEnabled(True)
        self.input_field.setEnabled(True)
        self.stop_btn.hide()
        self.typing_label.hide()
        self._current_bubble = None
        self._scroll_to_bottom()

    def _on_error(self, error_msg: str):
        if self._current_bubble:
            self._current_bubble.append_text(f"\n\n❌ Error: {error_msg}")
        self._on_generation_done()

    def _stop_generation(self):
        if self._worker and self._worker.isRunning():
            self._worker.stop()
            self._worker.quit()
            self._worker.wait()
        self._on_generation_done()

    # ── Bubble Helpers ────────────────────────────────────────────────────────

    def _add_user_bubble(self, text: str) -> ChatBubble:
        bubble = ChatBubble(text, is_user=True)
        # Insert before the trailing stretch
        count = self.messages_layout.count()
        self.messages_layout.insertWidget(count - 1, bubble)
        QTimer.singleShot(10, self._scroll_to_bottom)
        return bubble

    def _add_assistant_bubble(self, text: str) -> ChatBubble:
        bubble = ChatBubble(text, is_user=False)
        count = self.messages_layout.count()
        self.messages_layout.insertWidget(count - 1, bubble)
        QTimer.singleShot(10, self._scroll_to_bottom)
        return bubble

    def _scroll_to_bottom(self):
        self.scroll_area.verticalScrollBar().setValue(
            self.scroll_area.verticalScrollBar().maximum()
        )

    def _clear_chat(self):
        self._history.clear()
        # Remove all bubbles (keep the trailing stretch)
        while self.messages_layout.count() > 1:
            item = self.messages_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._add_assistant_bubble("Chat cleared. How can I help you?")

    def closeEvent(self, event):
        if self._worker and self._worker.isRunning():
            self._worker.stop()
            self._worker.quit()
            self._worker.wait()
        event.accept()