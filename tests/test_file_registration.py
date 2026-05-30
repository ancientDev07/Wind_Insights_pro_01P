# tests/test_file_registration.py
"""File type registration tests"""
import pytest, os
from register_filetype import FileTypeRegistrar

@pytest.mark.skipif(os.name != 'nt', reason="Windows only")
def test_registrar_initialization():
    """Test registrar initialization"""
    registrar = FileTypeRegistrar()
    assert registrar.extension == ".wdip"
    assert registrar.prog_id == "WindDataInsightPro.Project"

@pytest.mark.skipif(os.name != 'nt', reason="Windows only")
@pytest.mark.admin_required
def test_register_development_mode():
    """Test registration in development mode"""
    registrar = FileTypeRegistrar()
    result = registrar.register(mode="development")
    
    if result:  # Only if admin rights available
        assert registrar.verify()
        registrar.unregister()
