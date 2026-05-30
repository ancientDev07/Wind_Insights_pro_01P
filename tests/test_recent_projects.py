# tests/test_recent_projects.py
"""Recent projects manager tests"""
import json, os
from utils.recent_projects_manager import RecentProjectsManager

def test_add_recent_project(temp_dir):
    """Test adding project to recent list"""
    manager = RecentProjectsManager()
    
    # Create dummy project file
    project_path = os.path.join(temp_dir, "test.wdip")
    with open(project_path, 'w') as f:
        json.dump({"metadata": {"name": "Test"}}, f)
    
    manager.add_recent_project(project_path)
    recent = manager.get_recent_projects()
    
    assert len(recent) > 0
    assert recent[0]['path'] == project_path

def test_remove_recent_project(temp_dir):
    """Test removing project from recent list"""
    manager = RecentProjectsManager()
    
    project_path = os.path.join(temp_dir, "test.wdip")
    with open(project_path, 'w') as f:
        json.dump({"metadata": {"name": "Test"}}, f)
    
    manager.add_recent_project(project_path)
    manager.remove_recent_project(project_path)
    
    recent = manager.get_recent_projects()
    paths = [p['path'] for p in recent]
    assert project_path not in paths

def test_recent_projects_limit(temp_dir):
    """Test recent projects list limit"""
    manager = RecentProjectsManager()
    
    # Add 15 projects
    for i in range(15):
        path = os.path.join(temp_dir, f"test_{i}.wdip")
        with open(path, 'w') as f:
            json.dump({"metadata": {"name": f"Test {i}"}}, f)
        manager.add_recent_project(path)
    
    recent = manager.get_recent_projects()
    assert len(recent) <= 10  # Should be limited to 10
