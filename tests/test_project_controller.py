# tests/test_project_controller.py
"""Project controller tests"""
import pytest
import json, os
from controllers.file_menu_controller import ProjectController
from PyQt5.QtWidgets import QMainWindow

@pytest.fixture
def mock_main_window(qapp):
    """Mock main window for controller"""
    window = QMainWindow()
    return window

def test_project_structure(mock_main_window):
    """Test default project structure"""
    controller = ProjectController(mock_main_window)
    project = controller._get_default_project_structure()
    
    assert 'metadata' in project
    assert 'data' in project
    assert 'analysis' in project
    assert 'visualizations' in project
    assert 'settings' in project

def test_save_project(mock_main_window, temp_dir):
    """Test project save functionality"""
    controller = ProjectController(mock_main_window)
    controller.current_project = controller._get_default_project_structure({
        "name": "Test Project"
    })
    
    save_path = os.path.join(temp_dir, "test_project.wdip")
    result = controller._perform_save(save_path)
    
    assert result is True
    assert os.path.exists(save_path)
    
    # Verify content
    with open(save_path, 'r') as f:
        data = json.load(f)
        assert data['metadata']['name'] == "Test Project"

def test_load_project(mock_main_window, temp_dir):
    """Test project load functionality"""
    # Create test project file
    project_data = {
        "metadata": {"name": "Test Load"},
        "data": {},
        "analysis": {},
        "visualizations": {},
        "settings": {}
    }
    
    project_path = os.path.join(temp_dir, "test_load.wdip")
    with open(project_path, 'w') as f:
        json.dump(project_data, f)
    
    controller = ProjectController(mock_main_window)
    loaded_data = controller._read_project_file(project_path)
    
    assert loaded_data['metadata']['name'] == "Test Load"
