# tests/test_ui_components.py
"""UI component tests"""
import pytest
from views.start.start_screen import StartScreen

def test_start_screen_creation(qapp):
    """Test start screen initialization"""
    screen = StartScreen()
    assert screen.windowTitle() == "Wind Data Insight Pro"
    screen.close()

def test_recent_table_creation(qapp):
    """Test recent projects table creation"""
    screen = StartScreen()
    table = screen.create_projects_table()
    
    assert table.columnCount() == 5  # #, Name, Location, Last Opened, Size
    assert table.horizontalHeaderItem(0).text() == "#"
    assert table.horizontalHeaderItem(1).text() == "Name"
    
    screen.close()

def test_project_card_creation(qapp):
    """Test project card widget creation"""
    screen = StartScreen()
    card = screen.create_project_card("📄", "Test Project")
    
    assert card is not None
    assert card.objectName() == "projectCard"
    
    screen.close()
