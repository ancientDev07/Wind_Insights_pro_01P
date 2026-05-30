# tests/test_database.py
"""Database manager tests"""
import pytest
import os
from controllers.database.database_manager import DatabaseManager

def test_database_initialization(test_db_path):
    """Test database creation and initialization"""
    db = DatabaseManager(test_db_path)
    assert db.connection is not None
    db.close()

def test_create_project(test_db_path, sample_project_data, sample_csv):
    """Test project creation from metadata"""
    db = DatabaseManager(test_db_path)
    
    project_id, turbines = db.create_project_from_metadata(
        sample_project_data, 
        sample_csv
    )
    
    assert project_id > 0
    assert len(turbines) > 0
    assert 'WTG_01' in turbines
    
    db.close()

def test_get_turbines(test_db_path, sample_project_data, sample_csv):
    """Test retrieving turbine list"""
    db = DatabaseManager(test_db_path)
    
    project_id, _ = db.create_project_from_metadata(
        sample_project_data, 
        sample_csv
    )
    
    turbines = db.get_turbines(project_id)
    assert len(turbines) > 0
    
    db.close()

def test_get_turbine_data(test_db_path, sample_project_data, sample_csv):
    """Test retrieving turbine data"""
    db = DatabaseManager(test_db_path)
    
    project_id, turbines = db.create_project_from_metadata(
        sample_project_data, 
        sample_csv
    )
    
    data = db.get_turbine_data(project_id, turbines[0])
    assert not data.empty
    assert 'wind_speed' in data.columns or any('wind' in col.lower() for col in data.columns)
    
    # Test timestamp parsing - should not have NaT values
    timestamp_cols = [col for col in data.columns if 'timestamp' in col.lower() or 'time' in col.lower()]
    if timestamp_cols:
        ts_col = timestamp_cols[0]
        # Check that timestamps are datetime type and not NaT
        assert pd.api.types.is_datetime64_any_dtype(data[ts_col]), f"Column {ts_col} should be datetime type"
        assert not data[ts_col].isna().all(), f"Column {ts_col} should not be all NaT"
    
    db.close()

def test_timestamp_parsing_with_different_formats(test_db_path, temp_dir):
    """Test timestamp parsing with various date formats"""
    import pandas as pd
    
    # Create test data with different timestamp formats
    df = pd.DataFrame({
        'timestamp': [
            '01-02-2024 10:00:00',  # DD-MM-YYYY
            '02-01-2024 11:00:00',  # Could be ambiguous
            '2024-03-01 12:00:00',  # ISO format
            '01/04/2024 13:00:00',  # MM/DD/YYYY
        ],
        'wtg_id': ['WTG_01'] * 4,
        'wind_speed': [5.5] * 4,
        'power': [1500] * 4
    })
    
    csv_path = os.path.join(temp_dir, "timestamp_test.csv")
    df.to_csv(csv_path, index=False)
    
    db = DatabaseManager(test_db_path)
    
    project_id, turbines = db.create_project_from_metadata({
        "name": "Timestamp Test",
        "location": "Test",
        "company": "Test",
        "capacity": "10 MW",
        "model_name": "Test"
    }, csv_path)
    
    data = db.get_turbine_data(project_id, 'WTG_01')
    
    # Check timestamp column exists and is properly parsed
    ts_cols = [col for col in data.columns if 'timestamp' in col.lower()]
    assert len(ts_cols) > 0, "Should have timestamp column"
    
    ts_col = ts_cols[0]
    assert pd.api.types.is_datetime64_any_dtype(data[ts_col]), f"Column {ts_col} should be datetime"
    # Allow some NaT values but not all
    assert not data[ts_col].isna().all(), f"Not all values should be NaT in {ts_col}"
    
    db.close()
