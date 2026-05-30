# tests/conftest.py - COMPLETE REVAMP
import pytest
import os
import sys
import tempfile
import shutil
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Qt availability check
try:
    from PyQt5.QtWidgets import QApplication
    HAS_QT = True
except:
    HAS_QT = False

# Fixtures
@pytest.fixture(scope="session")
def qapp():
    """QApplication for all UI tests"""
    if not HAS_QT:
        pytest.skip("PyQt5 not available")
    
    app = QApplication.instance() or QApplication(sys.argv)
    yield app
    app.quit()

@pytest.fixture
def temp_dir():
    """Temporary directory"""
    temp = tempfile.mkdtemp()
    yield temp
    shutil.rmtree(temp, ignore_errors=True)

@pytest.fixture
def test_db_path(temp_dir):
    """Test database path"""
    return os.path.join(temp_dir, "test.db")

@pytest.fixture
def sample_project_data():
    """Sample project metadata"""
    return {
        "name": "Test Project",
        "location": "Test Site",
        "company": "Test Co",
        "capacity": "100 MW",
        "model_name": "Test Model"
    }

@pytest.fixture
def sample_csv(temp_dir):
    """Sample CSV file"""
    import pandas as pd
    
    df = pd.DataFrame({
        'timestamp': pd.date_range('2024-01-01', periods=50, freq='10min'),
        'wtg_id': ['WTG_01'] * 50,
        'wind_speed': [5.5] * 50,
        'power': [1500] * 50
    })
    
    path = os.path.join(temp_dir, "data.csv")
    df.to_csv(path, index=False)
    return path

@pytest.fixture
def sample_wdip_file(temp_dir):
    """Sample .wdip project file"""
    data = {
        "metadata": {"name": "Test", "created_date": "2024-01-01"},
        "db_id": 1
    }
    path = os.path.join(temp_dir, "test.wdip")
    with open(path, 'w') as f:
        json.dump(data, f)
    return path

# Markers
def pytest_configure(config):
    config.addinivalue_line("markers", "ui: UI tests requiring display")
    config.addinivalue_line("markers", "slow: slow tests")
    config.addinivalue_line("markers", "admin: requires admin privileges")
