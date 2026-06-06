"""
Main QMainWindow.
"""
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
import os
from config import RESOURCE_DIR
from ui.dashboard.widget import DashboardWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DPOS - Desktop Personal OS")
        
        # Set Window Icon
        icon_path = os.path.join(RESOURCE_DIR, "assets", "icons", "app_icon.ico")
        self.setWindowIcon(QIcon(icon_path))
        
        # Set window attributes for glassmorphic/frameless overlay styling
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        
        # Central widget and layout setup
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)
        
        layout = QVBoxLayout(self.central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Embed the DashboardWidget in compact mode by default
        self.dashboard = DashboardWidget(compact_mode=True, parent=self)
        layout.addWidget(self.dashboard)
        
        # Match size to widget dimensions
        self.setFixedSize(self.dashboard.size())
