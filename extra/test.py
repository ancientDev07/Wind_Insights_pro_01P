import sys
import os
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
from PyQt5.QtCore import QUrl, QThread, pyqtSignal
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PyQt5.QtWebEngineWidgets import QWebEngineView

# 1. Configuration
PORT = 8000
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))  # Serve files from current script directory

class LocalServerThread(QThread):
    """
    Runs a simple HTTP server in a separate thread.
    """
    def run(self):
        # Change directory to where your HTML files are located
        os.chdir(ROOT_DIR)
        
        # Create the server
        self.httpd = HTTPServer(('localhost', PORT), SimpleHTTPRequestHandler)
        print(f"Serving at http://localhost:{PORT}")
        self.httpd.serve_forever()

    def stop(self):
        """Stops the server properly."""
        if hasattr(self, 'httpd'):
            self.httpd.shutdown()
            self.httpd.server_close()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyQt5 Localhost Render")
        self.resize(1024, 768)

        # 2. Start the Local Server
        self.server_thread = LocalServerThread()
        self.server_thread.start()

        # 3. Setup QWebEngineView
        self.browser = QWebEngineView()
        
        # Point the browser to localhost
        # Ensure 'index.html' exists in the same folder as this script
        local_url = f"http://localhost:{PORT}/index.html"
        self.browser.setUrl(QUrl(local_url))

        # Layout setup
        layout = QVBoxLayout()
        layout.addWidget(self.browser)
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def closeEvent(self, event):
        """
        Handle app closure to stop the server thread gracefully.
        """
        self.server_thread.stop()
        self.server_thread.wait()
        event.accept()

if __name__ == "__main__":
    # Create a dummy index.html if it doesn't exist
    if not os.path.exists("index.html"):
        with open("index.html", "w") as f:
            f.write("<h1>Hello from Localhost!</h1><p>This is rendered via Python http.server.</p>")

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())