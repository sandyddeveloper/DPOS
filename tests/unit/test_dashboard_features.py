import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
import arrow

from ui.dashboard import greeting
from modules.projects import service_checker
from modules.projects import git_watcher
from modules.monitor import collector
from modules.monitor import alerts

# 1. Greeting tests
def test_greeting_morning():
    with patch('ui.dashboard.greeting.datetime') as mock_date:
        mock_date.now.return_value = MagicMock(hour=8)
        assert greeting.get_greeting() == "Good Morning"

def test_greeting_afternoon():
    with patch('ui.dashboard.greeting.datetime') as mock_date:
        mock_date.now.return_value = MagicMock(hour=14)
        assert greeting.get_greeting() == "Good Afternoon"

def test_greeting_evening():
    with patch('ui.dashboard.greeting.datetime') as mock_date:
        mock_date.now.return_value = MagicMock(hour=19)
        assert greeting.get_greeting() == "Good Evening"

def test_greeting_night():
    with patch('ui.dashboard.greeting.datetime') as mock_date:
        mock_date.now.return_value = MagicMock(hour=23)
        assert greeting.get_greeting() == "Good Night"

def test_formatted_date():
    formatted = greeting.get_formatted_date()
    expected = arrow.now().format("dddd, D MMMM YYYY")
    assert formatted == expected


# 2. Alerts tests
def test_alerts_green():
    assert alerts.get_progress_bar_color(50.0) == "#2A9D8F"
    assert alerts.get_progress_bar_color(75.0) == "#2A9D8F"

def test_alerts_amber():
    assert alerts.get_progress_bar_color(75.1) == "#FFB703"
    assert alerts.get_progress_bar_color(90.0) == "#FFB703"

def test_alerts_red():
    assert alerts.get_progress_bar_color(90.1) == "#E63946"


# 3. Collector tests
@patch('psutil.cpu_percent')
@patch('psutil.virtual_memory')
def test_collector_snapshot(mock_virtual_memory, mock_cpu_percent):
    mock_cpu_percent.return_value = 45.5
    
    mock_ram = MagicMock()
    mock_ram.percent = 60.2
    mock_ram.used = 8 * (1024 ** 3)
    mock_ram.total = 16 * (1024 ** 3)
    mock_virtual_memory.return_value = mock_ram
    
    snapshot = collector.get_snapshot()
    assert snapshot["cpu_percent"] == 45.5
    assert snapshot["ram_percent"] == 60.2
    assert snapshot["ram_used_gb"] == 8.0
    assert snapshot["ram_total_gb"] == 16.0


# 4. Service checker tests
@patch('psutil.net_connections')
def test_check_port_open_psutil_success(mock_net_conn):
    mock_conn = MagicMock()
    mock_conn.laddr = MagicMock(port=8000)
    mock_net_conn.return_value = [mock_conn]
    
    assert service_checker.check_port_open(8000) is True

@patch('psutil.net_connections', side_effect=Exception("Access Denied"))
@patch('socket.socket')
def test_check_port_open_socket_fallback(mock_socket, mock_net_conn):
    mock_s = MagicMock()
    mock_s.connect_ex.return_value = 0
    mock_socket.return_value.__enter__.return_value = mock_s
    
    assert service_checker.check_port_open(8000) is True

@patch('psutil.process_iter')
def test_check_process_running(mock_proc_iter):
    mock_proc = MagicMock()
    mock_proc.info = {'name': 'Python.exe'}
    mock_proc_iter.return_value = [mock_proc]
    
    assert service_checker.check_process_running('python.exe') is True
    assert service_checker.check_process_running('node') is False


# 5. Git watcher tests
@patch('modules.projects.git_watcher.Repo')
def test_git_changes_count(mock_repo_class):
    mock_project = MagicMock()
    mock_project.path = "/fake/path"
    
    mock_repo = MagicMock()
    mock_repo.index.diff.return_value = [1, 2]
    mock_repo.untracked_files = [3]
    mock_repo_class.return_value = mock_repo
    
    changes = git_watcher.get_git_changes_count([mock_project])
    assert changes == 3


# 6. Dashboard navigation and fullscreen tests
@patch('ui.dashboard.widget.SessionLocal')
@patch('ui.dashboard.widget.greeting')
@patch('ui.dashboard.widget.collector')
def test_dashboard_card_and_gauge_navigation(mock_collector, mock_greeting, mock_session, qtbot):
    # Setup mocks
    mock_greeting.get_greeting.return_value = "Hello"
    mock_greeting.get_formatted_date.return_value = "Saturday, 6 June 2026"
    mock_collector.get_snapshot.return_value = {
        "cpu_percent": 10.0,
        "ram_percent": 20.0,
        "ram_used_gb": 4.0,
        "ram_total_gb": 16.0
    }
    
    # Instantiate widget
    from ui.dashboard.widget import DashboardWidget
    from PyQt6.QtWidgets import QMainWindow
    
    # We need a dummy main window to act as self.window()
    win = QMainWindow()
    widget = DashboardWidget(compact_mode=True, parent=win)
    win.setCentralWidget(widget)
    qtbot.addWidget(win)
    
    # Assert initial state
    assert widget.compact_mode is True
    assert widget.stacked_widget.currentIndex() == 0
    
    # Trigger on_card_clicked for active projects
    widget.on_card_clicked("active")
    assert widget.stacked_widget.currentIndex() == 1
    assert widget.compact_mode is False
    
    # Set back to compact and test clips card
    widget.compact_mode = True
    widget.switch_page(0)
    widget.on_card_clicked("clips")
    assert widget.stacked_widget.currentIndex() == 2
    assert widget.compact_mode is False
    
    # Set back to compact and test gauge click
    widget.compact_mode = True
    widget.switch_page(0)
    widget.on_gauge_clicked()
    assert widget.stacked_widget.currentIndex() == 3
    assert widget.compact_mode is False


@patch('ui.dashboard.widget.SessionLocal')
@patch('ui.dashboard.widget.greeting')
@patch('ui.dashboard.widget.collector')
def test_dashboard_fullscreen_toggle(mock_collector, mock_greeting, mock_session, qtbot):
    mock_greeting.get_greeting.return_value = "Hello"
    mock_greeting.get_formatted_date.return_value = "Saturday, 6 June 2026"
    mock_collector.get_snapshot.return_value = {
        "cpu_percent": 10.0,
        "ram_percent": 20.0,
        "ram_used_gb": 4.0,
        "ram_total_gb": 16.0
    }
    
    from ui.dashboard.widget import DashboardWidget
    from PyQt6.QtWidgets import QMainWindow
    
    win = QMainWindow()
    widget = DashboardWidget(compact_mode=True, parent=win)
    win.setCentralWidget(widget)
    qtbot.addWidget(win)
    
    # Patch isFullScreen and showFullScreen / showNormal
    win.isFullScreen = MagicMock(return_value=False)
    win.showFullScreen = MagicMock()
    win.showNormal = MagicMock()
    
    # Toggle to fullscreen
    widget.toggle_fullscreen()
    assert widget.was_compact_before_fullscreen is True
    assert widget.compact_mode is False
    win.showFullScreen.assert_called_once()
    
    # Toggle back from fullscreen
    win.isFullScreen.return_value = True
    widget.toggle_fullscreen()
    assert widget.compact_mode is True
    assert win.showNormal.call_count == 2


