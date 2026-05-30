# views/components/instructions_widget.py
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel

class InstructionsWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        instructions = QLabel("""
        <h2>How to Use the App</h2>
        <p>1. Import your data using the 'Import Data' option in the File menu.</p>
        <p>2. Make sure your file should have date format of "DD-MM-YYYY", not "MM-DD-YYYY".</p>
        <p>3. Perform analysis using the Analysis menu.</p>
        <p>4. Visualize your data using the Visualization menu.</p>
        <p>5. Save or export your results using the File menu.</p>
        """)
        instructions.setWordWrap(True)
        instructions.setOpenExternalLinks(True)
        layout.addWidget(instructions)
        self.setLayout(layout)