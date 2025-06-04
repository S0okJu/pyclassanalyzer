import tempfile
from pathlib import Path
import pytest
from pyclass_analyzer.collector import PackageCollector

@pytest.fixture
def init_does_not_exist_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        package = base / "pyclass_analyzer"
        package.mkdir()
        (package / "main.py").write_text("# main")
        (package / "utils.py").write_text("# utils")
        yield base

@pytest.fixture
def temp_python_files():
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        package = base / "pyclass_analyzer"
        package.mkdir()
        (package / "main.py").write_text("# main")
        (package / "utils.py").write_text("# utils")
        (package / "__init__.py").write_text("# init")

        (base / "script.py").write_text("# top-level script")

        yield base
    


class TestPackageCollector:
    
    def test__collect_general_package_success(self, temp_python_files):
        collector = PackageCollector(str(temp_python_files))
        collector._collect_general_package()

        assert len(collector._packages) == 1
        assert "pyclass_analyzer" in collector._packages

    def test__collect_general_package_init_does_not_exist(self, init_does_not_exist_dir):
        collector = PackageCollector(str(init_does_not_exist_dir))
        collector._collect_general_package()

        assert len(collector._packages) == 0
    
    def test__collect_top_package_success(self, temp_python_files):
        collector = PackageCollector(str(temp_python_files))
        collector._collect_top_package()

        assert len(collector._packages) == 1
    
    def test_collect_success(self, temp_python_files):
        collector = PackageCollector(str(temp_python_files))
        collector.collect()

        assert len(collector._packages) == 2
        assert "pyclass_analyzer" in collector._packages
    
    
        
        
    
    