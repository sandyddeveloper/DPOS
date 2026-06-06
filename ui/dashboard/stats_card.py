"""
Reusable stat card component.
"""
from PyQt6.QtWidgets import QFrame, QVBoxLayout, QLabel, QGraphicsDropShadowEffect
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

class StatsCard(QFrame):
    def __init__(self, title: str, value: str = "0", parent=None):
        super().__init__(parent)
        self.setObjectName("StatsCard")
        
        # Configure layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(4)
        
        # Title Label (Uppercase for stats design)
        self.title_label = QLabel(title.upper())
        self.title_label.setObjectName("StatsCardTitle")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        
        # Value Label
        self.value_label = QLabel(value)
        self.value_label.setObjectName("StatsCardValue")
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        
        layout.addWidget(self.title_label)
        layout.addWidget(self.value_label)
        
        # Soft Drop Shadow for premium depth
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(10)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(0, 3)
        self.setGraphicsEffect(shadow)
        
        # Modern, compact dark card styling
        self.setStyleSheet("""
            #StatsCard {
                background-color: rgba(30, 30, 46, 0.7);
                border: 1px solid rgba(48, 48, 70, 0.5);
                border-radius: 8px;
            }
            #StatsCardTitle {
                color: #8C8C9E;
                font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif;
                font-size: 9px;
                font-weight: 700;
                letter-spacing: 0.8px;
            }
            #StatsCardValue {
                color: #00E5FF;
                font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif;
                font-size: 22px;
                font-weight: 700;
            }
        """)

    def set_value(self, value: str):
        self.value_label.setText(value)
        
    def set_title(self, title: str):
        self.title_label.setText(title.upper())

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            parent = self.parent()
            while parent:
                if hasattr(parent, "on_card_clicked"):
                    parent.on_card_clicked(self.title_label.text().lower())
                    break
                parent = parent.parent()
            event.accept()

