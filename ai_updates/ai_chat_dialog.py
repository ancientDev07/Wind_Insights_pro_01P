"""AI Analysis Dialog with RAG Support"""
import logging
from pathlib import Path

from PyQt5.QtCore import QUrl, pyqtSlot, pyqtSignal, QObject, QThread
from PyQt5.QtWebChannel import QWebChannel
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWidgets import *

from config.rag_config import RAGConfig
from rag.pipeline import RAGPipeline

logger = logging.getLogger(__name__)

# ── Top-level, alongside _LLMWorker and _ConnectionWorker ──

class _IndexWorker(QThread):
    """Runs document indexing off the main thread."""
    done = pyqtSignal(bool, int)   # (success, chunk_count)
    err  = pyqtSignal(str)

    def __init__(self, pipeline, path):
        self._pipeline = pipeline
        self._path = path

    def run(self):
        try:
            self._pipeline.build(self._path, force_rebuild=True)
            self.done.emit(True, self._pipeline.chunk_count)
        except Exception as e:
            self.err.emit(str(e))
            self.done.emit(False, 0)

class LLMWorker(QThread):
    """Runs blocking RAG/Ollama calls off the main thread."""
    response_ready = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self, message, pipeline, use_rag, ollama_host, model_name):
        self.message = message
        self.pipeline = pipeline
        self.use_rag = use_rag
        self.ollama_host = ollama_host
        self.model_name = model_name

    def run(self):
        try:
            if self.use_rag and self.pipeline:
                resp = self.pipeline.query(self.message, top_k=5)
                sources = "\n\nSources:\n" + "\n".join(f"- {s}" for s in resp.sources)
                self.response_ready.emit(resp.answer + sources)
            else:
                self._call_ollama()
        except Exception as e:
            self.error_occurred.emit(str(e))

    def _call_ollama(self):
        import requests
        try:
            try:
                tags = requests.get(f"{self.ollama_host}/api/tags", timeout=3)
                if tags.ok:
                    available = [m["name"] for m in tags.json().get("models", [])]
                    if not any(self.model_name in n for n in available):
                        self.error_occurred.emit(
                            f"Model '{self.model_name}' not found.\n"
                            f"Available: {', '.join(available)}\n"
                            f"Run: ollama pull {self.model_name}"
                        )
                        return
            except Exception:
                pass

            r = requests.post(
                f"{self.ollama_host}/api/chat",
                json={"model": self.model_name,
                      "messages": [{"role": "user", "content": self.message}],
                      "stream": False},
                timeout=120,
            )
            if r.status_code == 404:
                r2 = requests.post(
                    f"{self.ollama_host}/api/generate",
                    json={"model": self.model_name, "prompt": self.message, "stream": False},
                    timeout=120,
                )
                if r2.ok:
                    self.response_ready.emit(r2.json().get("response", "No response"))
                    return
            if r.ok:
                self.response_ready.emit(r.json().get("message", {}).get("content", "No response"))
            else:
                self.error_occurred.emit(f"HTTP {r.status_code}: {r.text[:300]}")
        except requests.exceptions.ConnectionError:
            self.error_occurred.emit(
                f"Cannot connect to Ollama at {self.ollama_host}.\nRun: ollama serve"
            )
        except Exception as e:
            self.error_occurred.emit(f"Error: {e}")


class ConnectionWorker(QThread):
    """Checks Ollama connectivity off the main thread."""
    status_update = pyqtSignal(str)
    connection_status = pyqtSignal(bool)

    def __init__(self, ollama_host, model_name):
        self.ollama_host = ollama_host
        self.model_name = model_name

    def run(self):
        import requests
        try:
            r = requests.get(f"{self.ollama_host}/api/tags", timeout=3)
            if r.status_code == 404:
                v = requests.get(f"{self.ollama_host}/api/version", timeout=3)
                if v.ok:
                    self.status_update.emit("Connected (older Ollama)")
                    self.connection_status.emit(True)
                    return
            if r.ok:
                models = r.json().get("models", [])
                found = any(self.model_name in m.get("name", "") for m in models)
                self.status_update.emit(
                    f"Connected — {len(models)} model(s)" if found
                    else f"Connected – model '{self.model_name}' not found"
                )
                self.connection_status.emit(found)
            else:
                self.status_update.emit(f"HTTP {r.status_code}")
                self.connection_status.emit(False)
        except requests.exceptions.ConnectionError:
            self.status_update.emit("Cannot connect to Ollama")
            self.connection_status.emit(False)
        except Exception:
            self.status_update.emit("Connection error")
            self.connection_status.emit(False)


class ChatBackend(QObject):
    statusUpdate = pyqtSignal(str)
    responseReceived = pyqtSignal(str)
    errorOccurred = pyqtSignal(str)
    connectionStatus = pyqtSignal(bool)
    indexingComplete = pyqtSignal(bool)   # ADD THIS LINE

    def __init__(self, parent=None):
        super().__init__(parent)
        self.pipeline = None
        self.rag_enabled = False
        self.ollama_host = "http://localhost:11434"
        self.model_name = "gemma4:e4b"
        self._workers = []    # ADD THIS LINE
        self._init_rag()
    
    def _init_rag(self):
        """Initialize RAG pipeline"""
        try:
            config = RAGConfig()
            self.pipeline = RAGPipeline(config)
            self.ollama_host = config.generator.ollama_base_url
            self.model_name = config.generator.ollama_model
            
            # Check if index exists
            index_path = Path(config.vector_store.persist_path)
            if index_path.exists() and (index_path / "index.faiss").exists():
                self.pipeline.build(str(index_path), force_rebuild=False)
                self.rag_enabled = True
                self.statusUpdate.emit("RAG system ready")
                logger.info("RAG pipeline loaded successfully")
            else:
                self.statusUpdate.emit("RAG index not found")
                logger.warning("RAG index not found")
        except Exception as e:
            logger.error(f"RAG init failed: {e}")
            self.statusUpdate.emit(f"RAG unavailable: {str(e)}")
    
    @pyqtSlot(str, bool)
    def sendMessage(self, message, use_rag):
        worker = LLMWorker(
            message, self.pipeline,
            use_rag and self.rag_enabled,
            self.ollama_host, self.model_name
        )
        worker.response_ready.connect(self.responseReceived)
        worker.error_occurred.connect(self.errorOccurred)
        worker.finished.connect(worker.deleteLater)
        worker.finished.connect(lambda w=worker: self._workers.remove(w) if w in self._workers else None)
        self._workers.append(worker)
        worker.start()
    
    def _call_ollama(self, message):
        """Direct Ollama call with better diagnostics"""
        try:
            import requests
            
            logger.info(f"Calling Ollama at {self.ollama_host}")
            
            # Try to get available models first
            try:
                models_response = requests.get(f"{self.ollama_host}/api/tags", timeout=3)
                if models_response.ok:
                    models = models_response.json().get('models', [])
                    available = [m['name'] for m in models]
                    logger.info(f"Available models: {available}")
                    
                    # Check if our model exists
                    model_exists = any(self.model_name in m for m in available)
                    if not model_exists:
                        error_msg = (
                            f"Model '{self.model_name}' not found.\n\n"
                            f"Available models: {', '.join(available)}\n\n"
                            f"Pull the model with:\n"
                            f"  ollama pull {self.model_name}"
                        )
                        self.errorOccurred.emit(error_msg)
                        return
            except Exception as e:
                logger.warning(f"Could not check models: {e}")
            
            # Make the chat request
            response = requests.post(
                f"{self.ollama_host}/api/chat",
                json={
                    "model": self.model_name,
                    "messages": [{"role": "user", "content": message}],
                    "stream": False
                },
                timeout=120
            )
            
            if response.status_code == 404:
                # Try alternative endpoint for older Ollama versions
                logger.warning("Chat API returned 404, trying generate endpoint")
                response = requests.post(
                    f"{self.ollama_host}/api/generate",
                    json={
                        "model": self.model_name,
                        "prompt": message,
                        "stream": False
                    },
                    timeout=120
                )
                
                if response.ok:
                    data = response.json()
                    content = data.get('response', 'No response')
                    self.responseReceived.emit(str(content))
                    return
            
            if response.ok:
                data = response.json()
                content = data.get('message', {}).get('content', 'No response')
                self.responseReceived.emit(str(content))
            else:
                error = (
                    f"HTTP {response.status_code}: {response.text}\n\n"
                    f"Endpoint: {self.ollama_host}/api/chat\n"
                    f"Model: {self.model_name}\n\n"
                    f"Check if Ollama is running:\n"
                    f"  ollama serve"
                )
                logger.error(error)
                self.errorOccurred.emit(error)
                
        except requests.exceptions.ConnectionError:
            error = (
                "Cannot connect to Ollama.\n\n"
                f"Host: {self.ollama_host}\n\n"
                "Make sure Ollama is running:\n"
                "  ollama serve\n\n"
                "Or check if the host URL is correct."
            )
            logger.error(error)
            self.errorOccurred.emit(error)
        except Exception as e:
            error = f"Error: {str(e)}"
            logger.error(f"Ollama call failed: {e}")
            self.errorOccurred.emit(error)

    @pyqtSlot()
    def checkConnection(self):
        worker = ConnectionWorker(self.ollama_host, self.model_name)
        worker.status_update.connect(self.statusUpdate)
        worker.connection_status.connect(self.connectionStatus)
        worker.finished.connect(worker.deleteLater) 
        worker.finished.connect(lambda w=worker: self._workers.remove(w) if w in self._workers else None)
        self._workers.append(worker)
        worker.start()
    
    @pyqtSlot(result=bool)
    def isRagEnabled(self):
        """Check if RAG is available"""
        return self.rag_enabled

    # ── Inside ChatBackend ──

    @pyqtSlot()
    def selectAndIndexDirectory(self):
        """Open native directory picker, then trigger indexing."""
        folder = QFileDialog.getExistingDirectory(
            None,
            "Select Document Directory",
            "",
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
        )
        if not folder:
            return  # User cancelled — do nothing
        self.indexDocuments(folder)

    @pyqtSlot(str)
    def indexDocuments(self, folder_path):
        if not self.pipeline:
            try:
                config = RAGConfig()
                self.pipeline = RAGPipeline(config)
            except Exception as e:
                self.errorOccurred.emit(f"Pipeline init failed: {e}")
                self.indexingComplete.emit(False)
                return

        self.statusUpdate.emit("Indexing documents...")

        worker = _IndexWorker(self.pipeline, folder_path)

        def _on_done(success, count):
            if success:
                self.rag_enabled = True
                self.statusUpdate.emit(f"Indexed {count} chunks")
            else:
                self.statusUpdate.emit("Indexing failed")
            self.indexingComplete.emit(success)
            if worker in self._workers:
                self._workers.remove(worker)

        worker.done.connect(_on_done)
        worker.err.connect(lambda e: self.errorOccurred.emit(f"Indexing failed: {e}"))
        worker.finished.connect(worker.deleteLater)   # AD
        self._workers.append(worker)
        worker.start()

    @pyqtSlot(str, str)
    def updateSettings(self, host, model):
        """Called from JS settings panel to sync host/model to Python backend."""
        self.ollama_host = host or "http://localhost:11434"
        self.model_name = model
        logger.info("Settings updated — host=%s model=%s", self.ollama_host, self.model_name)


class AIChatDialog(QDialog):
    """AI Chat Dialog with Web Interface"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("AI Assistant")
        self.resize(1000, 700)
        
        # Setup layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Web view
        self.web_view = QWebEngineView()
        layout.addWidget(self.web_view)
        
        # Setup web channel
        self.channel = QWebChannel()
        self.backend = ChatBackend(self)
        self.channel.registerObject("chatBackend", self.backend)
        self.web_view.page().setWebChannel(self.channel)
        
        # Load HTML
        html_path = Path(__file__).parent / "ai_chat.html"
        if html_path.exists():
            self.web_view.setUrl(QUrl.fromLocalFile(str(html_path)))
        else:
            logger.error(f"HTML file not found: {html_path}")
