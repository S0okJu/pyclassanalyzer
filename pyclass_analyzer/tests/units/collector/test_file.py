import tempfile
import pytest
from pathlib import Path

from pyclass_analyzer.collector import FileCollector
from pyclass_analyzer.types import ProjectPath

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


class TestFileCollector:
    def test__convert_module_path(self):
        base_path = "/Users/user/project"
        full_path = "/Users/user/project/pyclass_analyzer/main.py"

        collector = FileCollector(base_path)
        module_path = collector._convert_module_path(full_path)

        assert module_path == "pyclass_analyzer.main"

    def test_file_collector_collect(self, temp_python_files):
        collector = FileCollector(str(temp_python_files))
        result = collector.collect()
    
        base = temp_python_files
        expected = [
            ProjectPath(
                full_path=str(base / "pyclass_analyzer" / "main.py"),
                module_path="pyclass_analyzer.main",
                filename="main.py"
            ),
            ProjectPath(
                full_path=str(base / "pyclass_analyzer" / "utils.py"),
                module_path="pyclass_analyzer.utils",
                filename="utils.py"
            ),
            ProjectPath(
                full_path=str(base / "script.py"),
                module_path="script",
                filename="script.py"
            ),
        ]
    
        # 순서 없이 비교하려면 set-like 비교
        assert sorted(result, key=lambda x: x.full_path) == sorted(expected, key=lambda x: x.full_path)