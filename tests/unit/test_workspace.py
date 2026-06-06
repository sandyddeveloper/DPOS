"""
Unit tests for workspace module.
"""
import pytest
from unittest.mock import patch, MagicMock
from modules.workspace import registry, launcher

def test_list_templates():
    templates = registry.list_templates()
    assert len(templates) >= 2
    names = [t.get("name") for t in templates]
    assert "Python FastAPI" in names
    assert "React Node" in names

def test_get_template():
    t = registry.get_template("Python FastAPI")
    assert t is not None
    assert t.get("name") == "Python FastAPI"

    t_invalid = registry.get_template("Non Existent")
    assert t_invalid is None

@patch("modules.workspace.launcher.run_cmd_async")
def test_launch_workspace(mock_run_cmd):
    mock_proc = MagicMock()
    mock_run_cmd.return_value = mock_proc
    
    services = [
        {"type": "command", "command": "echo test"}
    ]
    
    launched = launcher.launch_workspace("test_proj", "/fake/path", services)
    assert len(launched) == 1
    assert launched[0] == mock_proc
    mock_run_cmd.assert_called_once_with("echo test", cwd="/fake/path")
    
    assert "test_proj" in launcher.get_running_workspaces()
    
    # Test stop
    launcher.stop_workspace("test_proj")
    mock_proc.terminate.assert_called_once()
    assert "test_proj" not in launcher.get_running_workspaces()
