"""
Projects panel.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QDialog, QLineEdit, QFormLayout, QScrollArea, QFrame, QGridLayout
)
from PyQt6.QtCore import Qt
from core.database import SessionLocal
from core.models import Project
from modules.projects import manager, service_checker, git_watcher
from modules.workspace.launcher import launch_workspace, stop_workspace

class AddProjectDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add New Project")
        self.setFixedSize(320, 240)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.CustomizeWindowHint | Qt.WindowType.WindowTitleHint | Qt.WindowType.WindowCloseButtonHint)
        self.setStyleSheet("""
            QDialog {
                background-color: #161622;
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 12px;
            }
            QLabel {
                color: #8C8C9E;
                font-family: 'Segoe UI', sans-serif;
                font-size: 11px;
                font-weight: 600;
            }
            QLineEdit {
                background-color: rgba(30, 30, 46, 0.8);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 6px;
                padding: 6px;
                color: #FFFFFF;
                font-family: 'Segoe UI', sans-serif;
                font-size: 11px;
            }
            QLineEdit:focus {
                border: 1px solid rgba(0, 229, 255, 0.5);
            }
            QPushButton {
                background-color: #2A9D8F;
                color: #FFFFFF;
                border: none;
                border-radius: 6px;
                padding: 8px;
                font-family: 'Segoe UI', sans-serif;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #35B0A1;
            }
        """)
        
        layout = QFormLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)
        
        self.name_edit = QLineEdit(self)
        self.name_edit.setPlaceholderText("e.g. My Website")
        
        self.path_edit = QLineEdit(self)
        self.path_edit.setPlaceholderText("e.g. C:\\Projects\\my_site")
        
        self.port_edit = QLineEdit(self)
        self.port_edit.setPlaceholderText("e.g. 8080 (optional)")
        
        layout.addRow("Project Name", self.name_edit)
        layout.addRow("Folder Path", self.path_edit)
        layout.addRow("TCP Port Monitoring", self.port_edit)
        
        self.btn_save = QPushButton("Add Project", self)
        self.btn_save.clicked.connect(self.accept)
        layout.addRow(self.btn_save)

class ProjectCard(QFrame):
    def __init__(self, project, on_changed_callback, parent=None):
        super().__init__(parent)
        self.project = project
        self.on_changed = on_changed_callback
        self.initUI()
        
    def initUI(self):
        self.setStyleSheet("""
            QFrame#ProjectCardOuter {
                background-color: rgba(30, 30, 46, 0.45);
                border: 1px solid rgba(255, 255, 255, 0.05);
                border-radius: 12px;
            }
            QFrame#ProjectCardOuter:hover {
                background-color: rgba(45, 45, 68, 0.6);
                border: 1px solid rgba(0, 229, 255, 0.25);
            }
        """)
        self.setObjectName("ProjectCardOuter")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)
        
        # Row 1: Title & Status Badge
        header = QHBoxLayout()
        
        name_lbl = QLabel(self.project.name)
        name_lbl.setStyleSheet("color: #FFFFFF; font-family: 'Segoe UI'; font-size: 13px; font-weight: bold;")
        
        is_active = service_checker.has_running_service(self.project)
        status_lbl = QLabel("ACTIVE" if is_active else "INACTIVE")
        status_color = "#2A9D8F" if is_active else "#E63946"
        status_lbl.setStyleSheet(f"""
            background-color: {status_color};
            color: #FFFFFF;
            font-family: 'Segoe UI';
            font-size: 8px;
            font-weight: bold;
            padding: 2px 6px;
            border-radius: 4px;
        """)
        
        header.addWidget(name_lbl)
        header.addWidget(status_lbl)
        header.addStretch()
        layout.addLayout(header)
        
        # Row 2: Path Link
        path_lbl = QLabel(self.project.path)
        path_lbl.setStyleSheet("color: #8C8C9E; font-family: 'Segoe UI'; font-size: 10px;")
        layout.addWidget(path_lbl)
        
        # Row 3: Git & Services info
        info_row = QHBoxLayout()
        git_changes = git_watcher.get_git_changes_count([self.project])
        git_lbl = QLabel(f"Git Changes: <b>{git_changes}</b>")
        git_lbl.setStyleSheet("color: #FFB703; font-family: 'Segoe UI'; font-size: 10px;")
        
        svc_count = len(self.project.services) if self.project.services else 0
        svc_lbl = QLabel(f"Services: <b>{svc_count}</b>")
        svc_lbl.setStyleSheet("color: #00E5FF; font-family: 'Segoe UI'; font-size: 10px;")
        
        info_row.addWidget(git_lbl)
        info_row.addWidget(svc_lbl)
        info_row.addStretch()
        layout.addLayout(info_row)
        
        # Row 4: Action Buttons
        actions = QHBoxLayout()
        actions.setSpacing(6)
        
        launch_btn = QPushButton("Launch Workspace")
        launch_btn.setStyleSheet("""
            QPushButton {
                background-color: #6200EE;
                color: #FFFFFF;
                font-family: 'Segoe UI';
                font-size: 10px;
                font-weight: 600;
                padding: 6px 12px;
                border-radius: 6px;
                border: none;
            }
            QPushButton:hover {
                background-color: #7A1EFA;
            }
        """)
        launch_btn.clicked.connect(self.launch)
        
        stop_btn = QPushButton("Stop")
        stop_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.08);
                color: #FFFFFF;
                font-family: 'Segoe UI';
                font-size: 10px;
                padding: 6px 12px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.15);
            }
        """)
        stop_btn.clicked.connect(self.stop)
        
        del_btn = QPushButton("Delete")
        del_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(230, 57, 70, 0.1);
                border: 1px solid rgba(230, 57, 70, 0.2);
                color: #E63946;
                font-family: 'Segoe UI';
                font-size: 10px;
                padding: 6px 12px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: rgba(230, 57, 70, 0.25);
                color: #FFFFFF;
            }
        """)
        del_btn.clicked.connect(self.delete_proj)
        
        actions.addWidget(launch_btn)
        actions.addWidget(stop_btn)
        actions.addWidget(del_btn)
        actions.addStretch()
        layout.addLayout(actions)
        
    def launch(self):
        services = self.project.services
        if not services:
            # Fallback mock service
            services = [{"type": "command", "command": "python -m http.server 9999"}]
        launch_workspace(self.project.name, self.project.path, services)
        self.on_changed()
        
    def stop(self):
        stop_workspace(self.project.name)
        self.on_changed()
        
    def delete_proj(self):
        session = SessionLocal()
        try:
            manager.delete_project(session, self.project.id)
        finally:
            session.close()
        self.on_changed()

class ProjectsPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()
        
    def initUI(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Header Row
        header = QHBoxLayout()
        title = QLabel("PROJECTS DASHBOARD")
        title.setStyleSheet("""
            color: #FFFFFF;
            font-family: 'Segoe UI';
            font-size: 16px;
            font-weight: 800;
        """)
        
        add_btn = QPushButton("+ New Project")
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: #2A9D8F;
                color: #FFFFFF;
                font-family: 'Segoe UI';
                font-size: 11px;
                font-weight: bold;
                padding: 6px 12px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #35B0A1;
            }
        """)
        add_btn.clicked.connect(self.add_project)
        
        header.addWidget(title)
        header.addWidget(add_btn)
        layout.addLayout(header)
        
        # Scroll Area for Project Cards
        self.scroll = QScrollArea(self)
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("""
            QScrollArea {
                background-color: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background-color: transparent;
                width: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: rgba(255, 255, 255, 0.1);
                border-radius: 3px;
            }
        """)
        
        self.scroll_content = QWidget()
        self.scroll_layout = QGridLayout(self.scroll_content)
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_layout.setSpacing(12)
        
        self.scroll.setWidget(self.scroll_content)
        layout.addWidget(self.scroll)
        
        self.refresh()
        
    def refresh(self):
        # Clear previous layout
        for i in reversed(range(self.scroll_layout.count())):
            widget = self.scroll_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
                
        session = SessionLocal()
        try:
            projects = manager.get_projects(session)
            for idx, p in enumerate(projects):
                card = ProjectCard(p, self.refresh, self)
                # Display cards in a 2-column grid layout
                row = idx // 2
                col = idx % 2
                self.scroll_layout.addWidget(card, row, col)
        finally:
            session.close()
            
    def add_project(self):
        dialog = AddProjectDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            name = dialog.name_edit.text().strip()
            path = dialog.path_edit.text().strip()
            port = dialog.port_edit.text().strip()
            
            if name and path:
                services = []
                if port:
                    try:
                        services.append({"type": "port", "port": int(port)})
                    except ValueError:
                        pass
                
                session = SessionLocal()
                try:
                    manager.create_project(session, name, path, services)
                finally:
                    session.close()
                self.refresh()
