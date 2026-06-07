"""
Dashboard widget.
"""
import os
import sys
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, 
    QGraphicsDropShadowEffect, QLineEdit, QListWidget, QListWidgetItem,
    QPushButton, QStackedWidget
)
from PyQt6.QtCore import QTimer, Qt, QRectF, QPoint
from PyQt6.QtGui import QColor, QPainter, QPen, QFont
import pyperclip

from ui.dashboard.stats_card import StatsCard
from ui.dashboard import greeting
from modules.projects import service_checker
from modules.projects import manager
from modules.projects import git_watcher
from modules.monitor import collector
from modules.monitor import alerts
from core.database import SessionLocal
from core.models import Project, ClipEntry
from utils.text_utils import sanitize_highlights

# Import feature panels
from ui.projects.panel import ProjectsPanel
from ui.clipboard.panel import ClipboardPanel
from ui.monitor.panel import SystemMonitorPanel

class CircularProgressBar(QWidget):
    def __init__(self, label: str, unit: str = "%", parent=None):
        super().__init__(parent)
        self.value = 0.0
        self.max_value = 100.0
        self.label_text = label
        self.unit = unit
        self.color = QColor("#2A9D8F")
        self.setMinimumSize(85, 85)
        self.setMaximumSize(120, 120)
        self._anim = None

    def set_value(self, target_value: float):
        from PyQt6.QtCore import QVariantAnimation, QEasingCurve
        
        # Stop any active animation
        if hasattr(self, "_anim") and self._anim and self._anim.state() == QVariantAnimation.State.Running:
            self._anim.stop()
            
        self._anim = QVariantAnimation(self)
        self._anim.setDuration(600)
        self._anim.setStartValue(self.value)
        self._anim.setEndValue(target_value)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        def update_val(val):
            self.value = val
            self.update()
            
        self._anim.valueChanged.connect(update_val)
        self._anim.start()

    def set_color(self, hex_color: str):
        self.color = QColor(hex_color)
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            parent = self.parent()
            while parent:
                if hasattr(parent, "on_gauge_clicked"):
                    parent.on_gauge_clicked()
                    break
                parent = parent.parent()
            event.accept()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        width = self.width()
        height = self.height()
        size = min(width, height) - 10
        x = (width - size) / 2
        y = (height - size) / 2

        rect = QRectF(x, y, size, size)

        # Draw dark track arc with a very clean dark color
        track_pen = QPen(QColor("rgba(30, 30, 46, 0.4)"), 5)
        painter.setPen(track_pen)
        painter.drawArc(rect, 0, 360 * 16)

        # Create gradient for active progress arc
        from PyQt6.QtGui import QLinearGradient
        gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
        gradient.setColorAt(0.0, self.color)
        
        # Shift CPU to neon cyan, RAM to neon pink/magenta
        if self.color.name().lower() == "#2a9d8f":
            gradient.setColorAt(1.0, QColor("#00E5FF"))  # Teal to Cyan
        elif self.color.name().lower() == "#ffb703":
            gradient.setColorAt(1.0, QColor("#FF2E93"))  # Yellow to Magenta
        else:
            gradient.setColorAt(1.0, self.color.lighter(130))

        # Draw active neon progress arc
        angle = int((self.value / self.max_value) * 360 * 16)
        active_pen = QPen(gradient, 6)
        active_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(active_pen)
        painter.drawArc(rect, 90 * 16, -angle)

        # Draw value text centered
        val_font = QFont("Segoe UI", 12, QFont.Weight.Bold)
        painter.setFont(val_font)
        painter.setPen(QColor("#FFFFFF"))
        val_rect = QRectF(x, y - 8, size, size)
        painter.drawText(val_rect, Qt.AlignmentFlag.AlignCenter, f"{self.value:.1f}{self.unit}")

        # Draw label text centered below
        lbl_font = QFont("Segoe UI", 7, QFont.Weight.Bold)
        painter.setFont(lbl_font)
        painter.setPen(QColor("#8C8C9E"))
        lbl_rect = QRectF(x, y + 14, size, size)
        painter.drawText(lbl_rect, Qt.AlignmentFlag.AlignCenter, self.label_text.upper())
        painter.end()


class SearchResultItemWidget(QWidget):
    def __init__(self, result, parent=None):
        super().__init__(parent)
        self.result = result
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(4)

        # Row 1: Type Badge + Title
        title_row = QHBoxLayout()
        title_row.setSpacing(8)

        self.badge_label = QLabel(result.doc_type.upper())
        self.badge_label.setStyleSheet(f"""
            background-color: {self.get_badge_color(result.doc_type)};
            color: #FFFFFF;
            font-family: 'Segoe UI', sans-serif;
            font-size: 8px;
            font-weight: bold;
            padding: 2px 6px;
            border-radius: 4px;
        """)
        
        self.title_label = QLabel(result.title)
        self.title_label.setStyleSheet("""
            color: #FFFFFF;
            font-family: 'Segoe UI', sans-serif;
            font-size: 11px;
            font-weight: 600;
        """)

        title_row.addWidget(self.badge_label)
        title_row.addWidget(self.title_label)
        title_row.addStretch()
        layout.addLayout(title_row)

        # Row 2: Subtitle
        self.sub_label = QLabel(result.subtitle)
        self.sub_label.setStyleSheet("""
            color: #8C8C9E;
            font-family: 'Segoe UI', sans-serif;
            font-size: 9px;
        """)
        layout.addWidget(self.sub_label)

        # Row 3: Highlights
        if result.highlights:
            clean_hl = sanitize_highlights(result.highlights)
            self.hl_label = QLabel(f"... {clean_hl} ...")
            self.hl_label.setStyleSheet("""
                color: #00E5FF;
                font-family: 'Segoe UI', sans-serif;
                font-size: 9px;
                font-style: italic;
            """)
            layout.addWidget(self.hl_label)

    def get_badge_color(self, doc_type: str) -> str:
        if doc_type == "project":
            return "#6200EE"
        elif doc_type == "code":
            return "#FF2E93"
        elif doc_type == "file":
            return "#00E5FF"
        elif doc_type == "clipboard":
            return "#FFB703"
        return "#777777"


from PyQt6.QtWidgets import QGraphicsOpacityEffect
from PyQt6.QtCore import QPropertyAnimation, QEasingCurve

class FadingStackedWidget(QStackedWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.fade_anim = None
        self.opacity_effect = None

    def setCurrentIndex(self, index: int):
        current_widget = self.currentWidget()
        next_widget = self.widget(index)
        if not next_widget or current_widget == next_widget:
            super().setCurrentIndex(index)
            return

        self.opacity_effect = QGraphicsOpacityEffect(next_widget)
        next_widget.setGraphicsEffect(self.opacity_effect)
        self.opacity_effect.setOpacity(0.0)

        self.fade_anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_anim.setDuration(220)
        self.fade_anim.setStartValue(0.0)
        self.fade_anim.setEndValue(1.0)
        self.fade_anim.setEasingCurve(QEasingCurve.Type.OutQuad)

        super().setCurrentIndex(index)
        self.fade_anim.start()

class DashboardWidget(QWidget):
    def __init__(self, compact_mode: bool = True, parent=None):
        super().__init__(parent)
        self.setObjectName("DashboardWidget")
        self.compact_mode = compact_mode
        self.last_date = ""
        self.drag_position = QPoint()
        
        self.initUI()
        self.start_timers()

    def get_qss_styles(self) -> str:
        """Returns the stylesheet configuration based on current compact_mode state."""
        if self.compact_mode:
            return """
                #DashboardWidget {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 rgba(22, 22, 36, 0.95), stop:1 rgba(14, 14, 24, 0.95));
                    border: 1px solid rgba(255, 255, 255, 0.08);
                    border-radius: 16px;
                }
                QPushButton#WindowCtrlBtn {
                    background-color: rgba(255, 255, 255, 0.05);
                    border: 1px solid rgba(255, 255, 255, 0.08);
                    border-radius: 6px;
                    color: #8C8C9E;
                    font-family: 'Segoe UI';
                    font-size: 11px;
                    width: 24px;
                    height: 24px;
                }
                QPushButton#WindowCtrlBtn:hover {
                    background-color: rgba(255, 255, 255, 0.15);
                    border: 1px solid rgba(0, 229, 255, 0.35);
                    color: #FFFFFF;
                }
                QPushButton#WindowCtrlBtnClose {
                    background-color: rgba(230, 57, 70, 0.15);
                    border: 1px solid rgba(230, 57, 70, 0.3);
                    border-radius: 6px;
                    color: #E63946;
                    font-family: 'Segoe UI';
                    font-size: 11px;
                    width: 24px;
                    height: 24px;
                }
                QPushButton#WindowCtrlBtnClose:hover {
                    background-color: rgba(230, 57, 70, 0.35);
                    color: #FFFFFF;
                }
            """
        else:
            return """
                #DashboardWidget {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #12121e, stop:1 #08080f);
                }
                QPushButton#WindowCtrlBtn {
                    background-color: rgba(255, 255, 255, 0.05);
                    border: 1px solid rgba(255, 255, 255, 0.08);
                    border-radius: 6px;
                    color: #8C8C9E;
                    font-family: 'Segoe UI';
                    font-size: 11px;
                    width: 28px;
                    height: 28px;
                }
                QPushButton#WindowCtrlBtn:hover {
                    background-color: rgba(255, 255, 255, 0.15);
                    border: 1px solid rgba(0, 229, 255, 0.35);
                    color: #FFFFFF;
                }
                QPushButton#WindowCtrlBtnClose {
                    background-color: rgba(230, 57, 70, 0.15);
                    border: 1px solid rgba(230, 57, 70, 0.3);
                    border-radius: 6px;
                    color: #E63946;
                    font-family: 'Segoe UI';
                    font-size: 11px;
                    width: 28px;
                    height: 28px;
                }
                QPushButton#WindowCtrlBtnClose:hover {
                    background-color: rgba(230, 57, 70, 0.35);
                    color: #FFFFFF;
                }
                
                #Sidebar {
                    background-color: rgba(20, 20, 30, 0.4);
                    border-right: 1px solid rgba(255, 255, 255, 0.04);
                }
                
                QPushButton#SidebarBtn {
                    background-color: transparent;
                    border: none;
                    color: #8C8C9E;
                    font-family: 'Segoe UI';
                    font-size: 11px;
                    font-weight: 600;
                    padding: 10px 14px;
                    text-align: left;
                    border-radius: 6px;
                }
                QPushButton#SidebarBtn:hover {
                    color: #FFFFFF;
                    background-color: rgba(255, 255, 255, 0.04);
                }
                QPushButton#SidebarBtn:checked {
                    color: #00E5FF;
                    background-color: rgba(0, 229, 255, 0.08);
                    border-left: 2px solid #00E5FF;
                    border-radius: 0px 6px 6px 0px;
                }
            """

    def initUI(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(14)
        
        self.setStyleSheet(self.get_qss_styles())
        if self.compact_mode:
            self.setFixedSize(360, 480)

        # 1. Header Layout (Horizontal containing text and window controls)
        header_outer_layout = QHBoxLayout()
        header_outer_layout.setContentsMargins(0, 0, 0, 0)
        header_outer_layout.setSpacing(10)
        
        # Stack Greeting & Date
        header_text_layout = QVBoxLayout()
        header_text_layout.setSpacing(2)
        
        self.greeting_label = QLabel("Good Morning")
        self.greeting_label.setObjectName("GreetingLabel")
        self.greeting_label.setStyleSheet(f"""
            #GreetingLabel {{
                color: #FFFFFF;
                font-family: 'Segoe UI', -apple-system, sans-serif;
                font-size: {"18px" if self.compact_mode else "26px"};
                font-weight: 700;
            }}
        """)
        
        self.date_label = QLabel("Saturday, 7 June 2026")
        self.date_label.setObjectName("DateLabel")
        self.date_label.setStyleSheet(f"""
            #DateLabel {{
                color: #8C8C9E;
                font-family: 'Segoe UI', -apple-system, sans-serif;
                font-size: {"10px" if self.compact_mode else "13px"};
                font-weight: 500;
            }}
        """)
        
        header_text_layout.addWidget(self.greeting_label)
        header_text_layout.addWidget(self.date_label)
        header_outer_layout.addLayout(header_text_layout)
        header_outer_layout.addStretch()
        
        # Window Controls Button Row
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(6)
        
        self.btn_minimize = QPushButton("—", self)
        self.btn_minimize.setToolTip("Minimize App")
        self.btn_minimize.setObjectName("WindowCtrlBtn")
        self.btn_minimize.clicked.connect(self.minimize_app)
        
        self.btn_widget = QPushButton("❐", self)
        self.btn_widget.setToolTip("Toggle Widget / Window Mode")
        self.btn_widget.setObjectName("WindowCtrlBtn")
        self.btn_widget.clicked.connect(self.toggle_widget_mode)
        
        self.btn_fullscreen = QPushButton("⛶", self)
        self.btn_fullscreen.setToolTip("Toggle Fullscreen")
        self.btn_fullscreen.setObjectName("WindowCtrlBtn")
        self.btn_fullscreen.clicked.connect(self.toggle_fullscreen)
        
        self.btn_close = QPushButton("✕", self)
        self.btn_close.setToolTip("Close App")
        self.btn_close.setObjectName("WindowCtrlBtnClose")
        self.btn_close.clicked.connect(self.close_app)
        
        controls_layout.addWidget(self.btn_minimize)
        controls_layout.addWidget(self.btn_widget)
        controls_layout.addWidget(self.btn_fullscreen)
        controls_layout.addWidget(self.btn_close)
        header_outer_layout.addLayout(controls_layout)
        
        main_layout.addLayout(header_outer_layout)
        
        # 2. Main split container (Horizontal containing Left Sidebar + Right StackedWidget)
        self.content_layout = QHBoxLayout()
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(10)
        
        # Left Sidebar (Hidden by default in compact mode)
        self.sidebar_widget = QFrame(self)
        self.sidebar_widget.setObjectName("Sidebar")
        self.sidebar_widget.setFixedWidth(110)
        
        sidebar_layout = QVBoxLayout(self.sidebar_widget)
        sidebar_layout.setContentsMargins(4, 10, 4, 10)
        sidebar_layout.setSpacing(8)
        
        self.btn_nav_dash = QPushButton("Dashboard")
        self.btn_nav_dash.setObjectName("SidebarBtn")
        self.btn_nav_dash.setCheckable(True)
        self.btn_nav_dash.setChecked(True)
        self.btn_nav_dash.clicked.connect(lambda: self.switch_page(0))
        
        self.btn_nav_proj = QPushButton("Projects")
        self.btn_nav_proj.setObjectName("SidebarBtn")
        self.btn_nav_proj.setCheckable(True)
        self.btn_nav_proj.clicked.connect(lambda: self.switch_page(1))
        
        self.btn_nav_clip = QPushButton("Clipboard")
        self.btn_nav_clip.setObjectName("SidebarBtn")
        self.btn_nav_clip.setCheckable(True)
        self.btn_nav_clip.clicked.connect(lambda: self.switch_page(2))
        
        self.btn_nav_mon = QPushButton("Sys Monitor")
        self.btn_nav_mon.setObjectName("SidebarBtn")
        self.btn_nav_mon.setCheckable(True)
        self.btn_nav_mon.clicked.connect(lambda: self.switch_page(3))
        
        sidebar_layout.addWidget(self.btn_nav_dash)
        sidebar_layout.addWidget(self.btn_nav_proj)
        sidebar_layout.addWidget(self.btn_nav_clip)
        sidebar_layout.addWidget(self.btn_nav_mon)
        sidebar_layout.addStretch()
        
        self.content_layout.addWidget(self.sidebar_widget)
        
        # Right Stacked Content Area
        self.stacked_widget = FadingStackedWidget(self)
        
        # Page 0: Compact Dashboard elements
        self.dashboard_panel = QWidget()
        dash_layout = QVBoxLayout(self.dashboard_panel)
        dash_layout.setContentsMargins(0, 0, 0, 0)
        dash_layout.setSpacing(14)
        
        # Universal Search Input Bar
        self.search_input = QLineEdit(self)
        self.search_input.setObjectName("SearchInput")
        self.search_input.setPlaceholderText("Search projects, files, code, clips...")
        self.search_input.setStyleSheet("""
            #SearchInput {
                background-color: rgba(30, 30, 46, 0.6);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 8px;
                padding: 6px 12px;
                color: #FFFFFF;
                font-family: 'Segoe UI', sans-serif;
                font-size: 11px;
            }
            #SearchInput:focus {
                border: 1px solid rgba(0, 229, 255, 0.5);
                background-color: rgba(30, 30, 46, 0.8);
            }
        """)
        self.search_input.textChanged.connect(self.on_search_text_changed)
        dash_layout.addWidget(self.search_input)

        # Stats Section
        self.stats_container = QWidget(self)
        stats_outer = QVBoxLayout(self.stats_container)
        stats_outer.setContentsMargins(0, 0, 0, 0)
        stats_outer.setSpacing(0)
        
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(8)
        self.projects_card = StatsCard("Active", "0", self)
        self.clips_card = StatsCard("Clips", "0", self)
        self.git_card = StatsCard("Changes", "0", self)
        stats_layout.addWidget(self.projects_card)
        stats_layout.addWidget(self.clips_card)
        stats_layout.addWidget(self.git_card)
        stats_outer.addLayout(stats_layout)
        dash_layout.addWidget(self.stats_container)
        
        # Resource Monitor Frame
        self.monitor_frame = QFrame(self)
        self.monitor_frame.setObjectName("MonitorFrame")
        self.monitor_frame.setStyleSheet("""
            #MonitorFrame {
                background-color: rgba(30, 30, 46, 0.5);
                border: 1px solid rgba(48, 48, 70, 0.4);
                border-radius: 12px;
            }
        """)
        
        monitor_layout = QVBoxLayout(self.monitor_frame)
        monitor_layout.setContentsMargins(12, 12, 12, 12)
        monitor_layout.setSpacing(10)
        
        monitor_title = QLabel("SYSTEM PERFORMANCE")
        monitor_title.setStyleSheet("""
            color: #8C8C9E;
            font-family: 'Segoe UI', -apple-system, sans-serif;
            font-size: 9px;
            font-weight: 700;
            letter-spacing: 0.8px;
        """)
        monitor_layout.addWidget(monitor_title)
        
        gauges_layout = QHBoxLayout()
        gauges_layout.setSpacing(16)
        self.cpu_gauge = CircularProgressBar("CPU", "%", self)
        self.ram_gauge = CircularProgressBar("RAM", "%", self)
        gauges_layout.addStretch()
        gauges_layout.addWidget(self.cpu_gauge)
        gauges_layout.addWidget(self.ram_gauge)
        gauges_layout.addStretch()
        monitor_layout.addLayout(gauges_layout)
        
        self.ram_details_label = QLabel("0.0 GB / 0.0 GB")
        self.ram_details_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.ram_details_label.setStyleSheet("""
            color: #8C8C9E;
            font-family: 'Segoe UI', sans-serif;
            font-size: 10px;
            font-weight: 500;
        """)
        monitor_layout.addWidget(self.ram_details_label)
        
        monitor_shadow = QGraphicsDropShadowEffect(self)
        monitor_shadow.setBlurRadius(10)
        monitor_shadow.setColor(QColor(0, 0, 0, 60))
        monitor_shadow.setOffset(0, 3)
        self.monitor_frame.setGraphicsEffect(monitor_shadow)
        dash_layout.addWidget(self.monitor_frame)

        # Search Results list (Hidden by default)
        self.search_results_list = QListWidget(self)
        self.search_results_list.setObjectName("SearchResultsList")
        self.search_results_list.setStyleSheet("""
            #SearchResultsList {
                background-color: rgba(30, 30, 46, 0.4);
                border: 1px solid rgba(48, 48, 70, 0.3);
                border-radius: 12px;
            }
            QListWidget::item {
                background-color: transparent;
                border-bottom: 1px solid rgba(48, 48, 70, 0.2);
            }
            QListWidget::item:hover {
                background-color: rgba(255, 255, 255, 0.03);
            }
            QListWidget::item:selected {
                background-color: rgba(0, 229, 255, 0.12);
                border-radius: 6px;
            }
        """)
        self.search_results_list.itemDoubleClicked.connect(self.on_item_double_clicked)
        self.search_results_list.setVisible(False)
        dash_layout.addWidget(self.search_results_list)
        
        if not self.compact_mode:
            dash_layout.addStretch()
            
        self.stacked_widget.addWidget(self.dashboard_panel)
        
        # Page 1: Projects Panel
        self.projects_panel = ProjectsPanel(self)
        self.stacked_widget.addWidget(self.projects_panel)
        
        # Page 2: Clipboard Panel
        self.clipboard_panel = ClipboardPanel(self)
        self.stacked_widget.addWidget(self.clipboard_panel)
        
        # Page 3: System Monitor Panel
        self.monitor_panel = SystemMonitorPanel(self)
        self.stacked_widget.addWidget(self.monitor_panel)
        
        self.content_layout.addWidget(self.stacked_widget)
        main_layout.addLayout(self.content_layout)

        # Initial visibility of sidebar
        self.sidebar_widget.setVisible(not self.compact_mode)

    # Drag-and-drop window movements for Top-Level widget bounds
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.window().frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.window().move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

    def switch_page(self, index: int):
        """Switches the stacked content layout view to the matching index."""
        self.stacked_widget.setCurrentIndex(index)
        
        self.btn_nav_dash.setChecked(index == 0)
        self.btn_nav_proj.setChecked(index == 1)
        self.btn_nav_clip.setChecked(index == 2)
        self.btn_nav_mon.setChecked(index == 3)
        
        # Refreshes contents on transition
        if index == 1:
            self.projects_panel.refresh()
        elif index == 2:
            self.clipboard_panel.refresh()
        elif index == 3:
            self.monitor_panel.refresh_metrics()
            self.monitor_panel.refresh_ports_and_docker()

    def on_card_clicked(self, card_title: str):
        title = card_title.strip().lower()
        if "active" in title or "changes" in title:
            self.switch_page(1)
            if self.compact_mode:
                self.toggle_widget_mode()
        elif "clips" in title or "clipboard" in title:
            self.switch_page(2)
            if self.compact_mode:
                self.toggle_widget_mode()

    def on_gauge_clicked(self):
        self.switch_page(3)
        if self.compact_mode:
            self.toggle_widget_mode()

    # Dynamic Window Control Buttons Actions
    def toggle_widget_mode(self):
        """Toggle between compact widget mode and normal window layout."""
        window = self.window()
        if not window:
            return
            
        self.compact_mode = not self.compact_mode
        self.setStyleSheet(self.get_qss_styles())
        
        if self.compact_mode:
            # Shift back to frameless on-top compact widget
            window.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
            window.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
            window.show()
            
            self.sidebar_widget.setVisible(False)
            self.switch_page(0)
            
            self.setMinimumSize(360, 480)
            self.setMaximumSize(360, 480)
            self.setFixedSize(360, 480)
            window.setMinimumSize(360, 480)
            window.setMaximumSize(360, 480)
            window.setFixedSize(360, 480)
            
            # Change label styling back to mini sizes
            self.greeting_label.setStyleSheet("""
                color: #FFFFFF; font-family: 'Segoe UI', sans-serif; font-size: 18px; font-weight: 700;
            """)
            self.date_label.setStyleSheet("""
                color: #8C8C9E; font-family: 'Segoe UI', sans-serif; font-size: 10px; font-weight: 500;
            """)
        else:
            # Keep it frameless and clean in windowed mode as well!
            window.setWindowFlags(Qt.WindowType.FramelessWindowHint)
            window.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
            window.show()
            
            self.sidebar_widget.setVisible(True)
            
            # Remove compact widget restrictions
            self.setMinimumSize(800, 600)
            self.setMaximumSize(16777215, 16777215)
            window.setMinimumSize(800, 600)
            window.setMaximumSize(16777215, 16777215)
            window.resize(800, 600)
            
            # Change label styling to standard sizes
            self.greeting_label.setStyleSheet("""
                color: #FFFFFF; font-family: 'Segoe UI', sans-serif; font-size: 26px; font-weight: 700;
            """)
            self.date_label.setStyleSheet("""
                color: #8C8C9E; font-family: 'Segoe UI', sans-serif; font-size: 13px; font-weight: 500;
            """)
            
        # Re-draw window properties
        window.activateWindow()

    def toggle_fullscreen(self):
        """Toggle fullscreen mode for the window."""
        window = self.window()
        if not window:
            return
            
        if window.isFullScreen():
            # If it was compact before fullscreen, restore compact mode
            if getattr(self, "was_compact_before_fullscreen", False):
                self.was_compact_before_fullscreen = False
                self.compact_mode = True
                self.setStyleSheet(self.get_qss_styles())
                self.sidebar_widget.setVisible(False)
                self.switch_page(0)
                
                self.setMinimumSize(360, 480)
                self.setMaximumSize(360, 480)
                self.setFixedSize(360, 480)
                window.setMinimumSize(360, 480)
                window.setMaximumSize(360, 480)
                window.setFixedSize(360, 480)
                
                self.greeting_label.setStyleSheet("""
                    color: #FFFFFF; font-family: 'Segoe UI', sans-serif; font-size: 18px; font-weight: 700;
                """)
                self.date_label.setStyleSheet("""
                    color: #8C8C9E; font-family: 'Segoe UI', sans-serif; font-size: 10px; font-weight: 500;
                """)
                
                # Restore frameless stays-on-top overlay flags on windows
                window.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
                window.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
                window.show()
            else:
                self.compact_mode = False
                self.setStyleSheet(self.get_qss_styles())
                self.sidebar_widget.setVisible(True)
                
                self.setMinimumSize(800, 600)
                self.setMaximumSize(16777215, 16777215)
                window.setMinimumSize(800, 600)
                window.setMaximumSize(16777215, 16777215)
                window.resize(800, 600)
                
                # Restore standard windowed flags (frameless)
                window.setWindowFlags(Qt.WindowType.FramelessWindowHint)
                window.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
                window.show()
        else:
            # We are going fullscreen
            if self.compact_mode:
                self.was_compact_before_fullscreen = True
                self.compact_mode = False
                self.setStyleSheet(self.get_qss_styles())
                self.sidebar_widget.setVisible(True)
                
                # Change label styling to standard sizes
                self.greeting_label.setStyleSheet("""
                    color: #FFFFFF; font-family: 'Segoe UI', sans-serif; font-size: 26px; font-weight: 700;
                """)
                self.date_label.setStyleSheet("""
                    color: #8C8C9E; font-family: 'Segoe UI', sans-serif; font-size: 13px; font-weight: 500;
                """)
            else:
                self.was_compact_before_fullscreen = False
                
            # Clear fixed size constraints before entering fullscreen
            self.setMinimumSize(0, 0)
            self.setMaximumSize(16777215, 16777215)
            window.setMinimumSize(0, 0)
            window.setMaximumSize(16777215, 16777215)
            
            # Keep it frameless during fullscreen
            window.setWindowFlags(Qt.WindowType.FramelessWindowHint)
            window.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
            window.show()
            window.showFullScreen()
            
    def close_app(self):
        """Close the window and exit."""
        window = self.window()
        if window:
            window.close()

    def minimize_app(self):
        """Minimize the window."""
        window = self.window()
        if window:
            window.showMinimized()

    def start_timers(self):
        self.stats_timer = QTimer(self)
        self.stats_timer.timeout.connect(self.refresh)
        self.stats_timer.start(3000)
        
        self.midnight_timer = QTimer(self)
        self.midnight_timer.timeout.connect(self.check_midnight)
        self.midnight_timer.start(60000)

    def showEvent(self, event):
        super().showEvent(event)
        self.render_dashboard()

    def render_dashboard(self):
        self.greeting_label.setText(greeting.get_greeting())
        self.last_date = greeting.get_formatted_date()
        self.date_label.setText(self.last_date)
        
        db_session = SessionLocal()
        try:
            projects = db_session.query(Project).all()
            
            clips_count = db_session.query(ClipEntry).count()
            self.clips_card.set_value(str(clips_count))
            
            git_changes = git_watcher.get_git_changes_count(projects)
            self.git_card.set_value(str(git_changes))
            
            active_count = service_checker.get_active_projects_count(projects)
            self.projects_card.set_value(str(active_count))
        except Exception as e:
            print(f"Error loading initial dashboard data: {e}")
        finally:
            db_session.close()
            
        self.update_system_metrics()

    def refresh(self):
        db_session = SessionLocal()
        try:
            projects = db_session.query(Project).all()
            active_count = service_checker.get_active_projects_count(projects)
            self.projects_card.set_value(str(active_count))
            
            git_changes = git_watcher.get_git_changes_count(projects)
            self.git_card.set_value(str(git_changes))
            
            clips_count = db_session.query(ClipEntry).count()
            self.clips_card.set_value(str(clips_count))
        except Exception as e:
            print(f"Error refreshing dashboard data: {e}")
        finally:
            db_session.close()
            
        self.update_system_metrics()

    def check_midnight(self):
        current_date = greeting.get_formatted_date()
        if current_date != self.last_date:
            self.greeting_label.setText(greeting.get_greeting())
            self.last_date = current_date
            self.date_label.setText(current_date)

    def update_system_metrics(self):
        snapshot = collector.get_snapshot()
        
        cpu_val = snapshot["cpu_percent"]
        ram_val = snapshot["ram_percent"]
        ram_used = snapshot["ram_used_gb"]
        ram_total = snapshot["ram_total_gb"]
        
        self.cpu_gauge.set_value(cpu_val)
        cpu_color = alerts.get_progress_bar_color(cpu_val)
        self.cpu_gauge.set_color(cpu_color)
        
        self.ram_gauge.set_value(ram_val)
        ram_color = alerts.get_progress_bar_color(ram_val)
        self.ram_gauge.set_color(ram_color)
        self.ram_details_label.setText(f"{ram_used:.1f} GB / {ram_total:.1f} GB")

    def on_search_text_changed(self, text: str):
        if not text.strip():
            self.search_results_list.setVisible(False)
            self.stats_container.setVisible(True)
            self.monitor_frame.setVisible(True)
            self.stats_timer.start(3000)
            self.render_dashboard()
        else:
            self.stats_container.setVisible(False)
            self.monitor_frame.setVisible(False)
            self.search_results_list.setVisible(True)
            self.stats_timer.stop()

            db_session = SessionLocal()
            try:
                from modules.search import searcher
                results = searcher.search(text, db_session)
                
                self.search_results_list.clear()
                for res in results:
                    item = QListWidgetItem(self.search_results_list)
                    widget = SearchResultItemWidget(res, self)
                    item.setSizeHint(widget.sizeHint())
                    self.search_results_list.addItem(item)
                    self.search_results_list.setItemWidget(item, widget)
            except Exception as e:
                print(f"Error querying search index: {e}")
            finally:
                db_session.close()

    def on_item_double_clicked(self, item: QListWidgetItem):
        widget = self.search_results_list.itemWidget(item)
        if not widget or not hasattr(widget, "result"):
            return
            
        res = widget.result
        if res.doc_type == "clipboard":
            try:
                clip_id = int(res.path.replace("clip_", ""))
                db_session = SessionLocal()
                try:
                    clip = db_session.query(ClipEntry).filter(ClipEntry.id == clip_id).first()
                    if clip:
                        pyperclip.copy(clip.content)
                        self.search_input.clear()
                        self.search_input.setPlaceholderText("Copied clip to clipboard!")
                finally:
                    db_session.close()
            except Exception as e:
                print(f"Error copying clip: {e}")
        else:
            if os.path.exists(res.path):
                try:
                    os.startfile(res.path)
                except Exception as e:
                    print(f"Error launching path: {e}")
