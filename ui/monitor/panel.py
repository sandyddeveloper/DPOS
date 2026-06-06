"""
System monitor panel.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, 
    QProgressBar, QFrame
)
from PyQt6.QtCore import QTimer, Qt
import psutil
import docker
from modules.monitor import collector, alerts

class SystemMonitorPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()
        self.start_timers()
        
    def initUI(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)
        
        # Title
        title = QLabel("SYSTEM PERFORMANCE MONITOR")
        title.setStyleSheet("""
            color: #FFFFFF;
            font-family: 'Segoe UI';
            font-size: 16px;
            font-weight: 800;
        """)
        layout.addWidget(title)
        
        # CPU & RAM Performance metrics
        self.metrics_frame = QFrame(self)
        self.metrics_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(30, 30, 46, 0.5);
                border: 1px solid rgba(48, 48, 70, 0.4);
                border-radius: 12px;
            }
        """)
        
        metrics_layout = QVBoxLayout(self.metrics_frame)
        metrics_layout.setContentsMargins(14, 14, 14, 14)
        metrics_layout.setSpacing(12)
        
        # CPU
        cpu_row = QHBoxLayout()
        cpu_title = QLabel("CPU Utilization")
        cpu_title.setStyleSheet("color: #FFFFFF; font-family: 'Segoe UI'; font-size: 11px; font-weight: bold;")
        self.cpu_lbl = QLabel("0.0%")
        self.cpu_lbl.setStyleSheet("color: #00E5FF; font-family: 'Segoe UI'; font-size: 11px; font-weight: bold;")
        cpu_row.addWidget(cpu_title)
        cpu_row.addStretch()
        cpu_row.addWidget(self.cpu_lbl)
        metrics_layout.addLayout(cpu_row)
        
        self.cpu_bar = QProgressBar(self)
        self.cpu_bar.setRange(0, 100)
        self.cpu_bar.setTextVisible(False)
        self.cpu_bar.setFixedHeight(8)
        self.cpu_bar.setStyleSheet("""
            QProgressBar {
                background-color: #1A1A28;
                border: none;
                border-radius: 4px;
            }
            QProgressBar::chunk {
                background-color: #2A9D8F;
                border-radius: 4px;
            }
        """)
        metrics_layout.addWidget(self.cpu_bar)
        
        # RAM
        ram_row = QHBoxLayout()
        ram_title = QLabel("RAM Utilization")
        ram_title.setStyleSheet("color: #FFFFFF; font-family: 'Segoe UI'; font-size: 11px; font-weight: bold;")
        self.ram_lbl = QLabel("0.0 GB / 0.0 GB (0%)")
        self.ram_lbl.setStyleSheet("color: #00E5FF; font-family: 'Segoe UI'; font-size: 11px; font-weight: bold;")
        ram_row.addWidget(ram_title)
        ram_row.addStretch()
        ram_row.addWidget(self.ram_lbl)
        metrics_layout.addLayout(ram_row)
        
        self.ram_bar = QProgressBar(self)
        self.ram_bar.setRange(0, 100)
        self.ram_bar.setTextVisible(False)
        self.ram_bar.setFixedHeight(8)
        self.ram_bar.setStyleSheet("""
            QProgressBar {
                background-color: #1A1A28;
                border: none;
                border-radius: 4px;
            }
            QProgressBar::chunk {
                background-color: #FFB703;
                border-radius: 4px;
            }
        """)
        metrics_layout.addWidget(self.ram_bar)
        
        layout.addWidget(self.metrics_frame)
        
        # Active services detail layout (listening ports & docker containers)
        cols = QHBoxLayout()
        cols.setSpacing(12)
        
        # Ports
        ports_box = QFrame(self)
        ports_box.setStyleSheet("""
            QFrame {
                background-color: rgba(30, 30, 46, 0.4);
                border: 1px solid rgba(48, 48, 70, 0.3);
                border-radius: 12px;
            }
        """)
        ports_layout = QVBoxLayout(ports_box)
        ports_layout.setContentsMargins(12, 12, 12, 12)
        ports_layout.setSpacing(8)
        
        ports_title = QLabel("ACTIVE LISTENING PORTS")
        ports_title.setStyleSheet("color: #8C8C9E; font-family: 'Segoe UI'; font-size: 9px; font-weight: bold; letter-spacing: 0.8px;")
        ports_layout.addWidget(ports_title)
        
        self.ports_list = QListWidget(self)
        self.ports_list.setStyleSheet("""
            QListWidget {
                background-color: transparent;
                border: none;
            }
            QListWidget::item {
                color: #FFFFFF;
                font-family: 'Consolas', monospace;
                font-size: 10px;
                padding: 4px 0px;
                border-bottom: 1px solid rgba(255,255,255,0.02);
            }
        """)
        ports_layout.addWidget(self.ports_list)
        cols.addWidget(ports_box)
        
        # Docker
        docker_box = QFrame(self)
        docker_box.setStyleSheet("""
            QFrame {
                background-color: rgba(30, 30, 46, 0.4);
                border: 1px solid rgba(48, 48, 70, 0.3);
                border-radius: 12px;
            }
        """)
        docker_layout = QVBoxLayout(docker_box)
        docker_layout.setContentsMargins(12, 12, 12, 12)
        docker_layout.setSpacing(8)
        
        docker_title = QLabel("DOCKER CONTAINER STATES")
        docker_title.setStyleSheet("color: #8C8C9E; font-family: 'Segoe UI'; font-size: 9px; font-weight: bold; letter-spacing: 0.8px;")
        docker_layout.addWidget(docker_title)
        
        self.docker_list = QListWidget(self)
        self.docker_list.setStyleSheet("""
            QListWidget {
                background-color: transparent;
                border: none;
            }
            QListWidget::item {
                color: #FFFFFF;
                font-family: 'Segoe UI', sans-serif;
                font-size: 10px;
                padding: 4px 0px;
                border-bottom: 1px solid rgba(255,255,255,0.02);
            }
        """)
        docker_layout.addWidget(self.docker_list)
        cols.addWidget(docker_box)
        
        layout.addLayout(cols)
        
        self.refresh_metrics()
        self.refresh_ports_and_docker()
        
    def start_timers(self):
        self.metrics_timer = QTimer(self)
        self.metrics_timer.timeout.connect(self.refresh_metrics)
        self.metrics_timer.start(2000)
        
        self.slow_timer = QTimer(self)
        self.slow_timer.timeout.connect(self.refresh_ports_and_docker)
        self.slow_timer.start(6000)
        
    def refresh_metrics(self):
        snapshot = collector.get_snapshot()
        cpu_val = snapshot["cpu_percent"]
        ram_val = snapshot["ram_percent"]
        ram_used = snapshot["ram_used_gb"]
        ram_total = snapshot["ram_total_gb"]
        
        self.cpu_bar.setValue(int(cpu_val))
        self.cpu_lbl.setText(f"{cpu_val:.1f}%")
        cpu_color = alerts.get_progress_bar_color(cpu_val)
        self.cpu_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: #1A1A28;
                border: none;
                border-radius: 4px;
            }}
            QProgressBar::chunk {{
                background-color: {cpu_color};
                border-radius: 4px;
            }}
        """)
        
        self.ram_bar.setValue(int(ram_val))
        self.ram_lbl.setText(f"{ram_used:.1f} GB / {ram_total:.1f} GB ({ram_val:.1f}%)")
        ram_color = alerts.get_progress_bar_color(ram_val)
        self.ram_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: #1A1A28;
                border: none;
                border-radius: 4px;
            }}
            QProgressBar::chunk {{
                background-color: {ram_color};
                border-radius: 4px;
            }}
        """)
        
    def refresh_ports_and_docker(self):
        # 1. Listening ports
        self.ports_list.clear()
        try:
            listen_ports = []
            for conn in psutil.net_connections(kind='inet'):
                if conn.status == 'LISTEN':
                    listen_ports.append(conn)
            # Sort by port number
            listen_ports.sort(key=lambda x: x.laddr.port)
            for conn in listen_ports[:10]:
                self.ports_list.addItem(f"Port {conn.laddr.port:<5} | PID {conn.pid or 'N/A'}")
        except Exception:
            self.ports_list.addItem("Port scanning permission denied or unavailable.")
            
        # 2. Docker container listing (handled gracefully if daemon is offline)
        self.docker_list.clear()
        try:
            client = docker.from_env()
            containers = client.containers.list(all=True)
            if not containers:
                self.docker_list.addItem("No containers found.")
            else:
                for c in containers[:10]:
                    self.docker_list.addItem(f"{c.name:<18} | {c.status.upper()}")
        except Exception:
            self.docker_list.addItem("Docker desktop daemon is offline.")
