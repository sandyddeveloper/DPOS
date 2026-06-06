"""
Clipboard panel.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QListWidget, QListWidgetItem, QPushButton
)
from PyQt6.QtCore import Qt
import pyperclip
from core.database import SessionLocal
from core.models import ClipEntry
from modules.clipboard.categories import detect_category
from utils.time_utils import format_relative_time
from utils.text_utils import truncate_text

class ClipItemWidget(QWidget):
    def __init__(self, clip, parent=None):
        super().__init__(parent)
        self.clip = clip
        self.initUI()
        
    def initUI(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(6)
        
        # Row 1: Category badge & relative timestamp
        header = QHBoxLayout()
        category = detect_category(self.clip.content)
        
        self.badge = QLabel(category.upper())
        self.badge.setStyleSheet(f"""
            background-color: {self.get_badge_color(category)};
            color: #FFFFFF;
            font-family: 'Segoe UI', sans-serif;
            font-size: 8px;
            font-weight: bold;
            padding: 2px 6px;
            border-radius: 4px;
        """)
        
        self.time_lbl = QLabel(format_relative_time(self.clip.timestamp))
        self.time_lbl.setStyleSheet("""
            color: #8C8C9E;
            font-family: 'Segoe UI', sans-serif;
            font-size: 9px;
            font-weight: 500;
        """)
        
        header.addWidget(self.badge)
        header.addWidget(self.time_lbl)
        header.addStretch()
        layout.addLayout(header)
        
        # Row 2: Text Snippet
        self.content_lbl = QLabel(truncate_text(self.clip.content, max_length=160))
        self.content_lbl.setStyleSheet("""
            color: #FFFFFF;
            font-family: 'Consolas', 'Courier New', monospace;
            font-size: 11px;
            line-height: 14px;
        """)
        layout.addWidget(self.content_lbl)
        
    def get_badge_color(self, category: str) -> str:
        colors = {
            "sql": "#6200EE",
            "url": "#00E5FF",
            "token": "#E63946",
            "code": "#FF2E93",
            "text": "#FFB703"
        }
        return colors.get(category, "#777777")

class ClipboardPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_filter = "ALL"
        self.initUI()
        
    def initUI(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        title = QLabel("CLIPBOARD MANAGER")
        title.setStyleSheet("""
            color: #FFFFFF;
            font-family: 'Segoe UI';
            font-size: 16px;
            font-weight: 800;
        """)
        layout.addWidget(title)
        
        # Search bar
        self.search_bar = QLineEdit(self)
        self.search_bar.setPlaceholderText("Search clipboard history...")
        self.search_bar.setStyleSheet("""
            QLineEdit {
                background-color: rgba(30, 30, 46, 0.6);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 8px;
                padding: 8px 12px;
                color: #FFFFFF;
                font-family: 'Segoe UI', sans-serif;
                font-size: 11px;
            }
            QLineEdit:focus {
                border: 1px solid rgba(0, 229, 255, 0.5);
                background-color: rgba(30, 30, 46, 0.8);
            }
        """)
        self.search_bar.textChanged.connect(self.refresh)
        layout.addWidget(self.search_bar)
        
        # Filter Buttons Row
        filters_layout = QHBoxLayout()
        filters_layout.setSpacing(6)
        
        self.filter_buttons = {}
        for f in ["ALL", "SQL", "URL", "CODE", "TEXT", "TOKEN"]:
            btn = QPushButton(f)
            btn.setCheckable(True)
            if f == "ALL":
                btn.setChecked(True)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: rgba(255, 255, 255, 0.04);
                    border: 1px solid rgba(255, 255, 255, 0.08);
                    color: #8C8C9E;
                    font-family: 'Segoe UI';
                    font-size: 9px;
                    font-weight: bold;
                    padding: 4px 10px;
                    border-radius: 6px;
                }
                QPushButton:hover {
                    background-color: rgba(255, 255, 255, 0.1);
                    color: #FFFFFF;
                }
                QPushButton:checked {
                    background-color: rgba(0, 229, 255, 0.12);
                    border: 1px solid #00E5FF;
                    color: #FFFFFF;
                }
            """)
            btn.clicked.connect(lambda checked, filter_name=f: self.set_filter(filter_name))
            filters_layout.addWidget(btn)
            self.filter_buttons[f] = btn
            
        filters_layout.addStretch()
        layout.addLayout(filters_layout)
        
        # Clipboard entries list
        self.list_widget = QListWidget(self)
        self.list_widget.setStyleSheet("""
            QListWidget {
                background-color: rgba(30, 30, 46, 0.4);
                border: 1px solid rgba(48, 48, 70, 0.3);
                border-radius: 12px;
            }
            QListWidget::item {
                background-color: transparent;
                border-bottom: 1px solid rgba(48, 48, 70, 0.2);
            }
            QListWidget::item:hover {
                background-color: rgba(255, 255, 255, 0.02);
            }
            QListWidget::item:selected {
                background-color: rgba(0, 229, 255, 0.1);
                border-radius: 6px;
            }
        """)
        self.list_widget.itemDoubleClicked.connect(self.copy_item)
        layout.addWidget(self.list_widget)
        
        self.refresh()
        
    def set_filter(self, filter_name: str):
        self.current_filter = filter_name
        for f, btn in self.filter_buttons.items():
            btn.setChecked(f == filter_name)
        self.refresh()
        
    def refresh(self):
        self.list_widget.clear()
        query = self.search_bar.text().strip()
        
        session = SessionLocal()
        try:
            if query:
                from modules.search import searcher
                results = searcher.search(query, session, doc_types=["clipboard"])
                clip_ids = []
                for r in results:
                    try:
                        clip_ids.append(int(r.path.replace("clip_", "")))
                    except ValueError:
                        pass
                
                clips = session.query(ClipEntry).filter(ClipEntry.id.in_(clip_ids)).all()
                clips_dict = {c.id: c for c in clips}
                clips = [clips_dict[cid] for cid in clip_ids if cid in clips_dict]
            else:
                clips = session.query(ClipEntry).order_by(ClipEntry.timestamp.desc()).limit(80).all()
                
            for c in clips:
                category = detect_category(c.content)
                if self.current_filter != "ALL" and category.upper() != self.current_filter:
                    continue
                    
                item = QListWidgetItem(self.list_widget)
                widget = ClipItemWidget(c, self)
                item.setSizeHint(widget.sizeHint())
                self.list_widget.addItem(item)
                self.list_widget.setItemWidget(item, widget)
        finally:
            session.close()
            
    def copy_item(self, item: QListWidgetItem):
        widget = self.list_widget.itemWidget(item)
        if widget and hasattr(widget, "clip"):
            pyperclip.copy(widget.clip.content)
            self.search_bar.clear()
            self.search_bar.setPlaceholderText("Copied historical entry back to clipboard!")
