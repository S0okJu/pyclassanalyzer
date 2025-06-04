from unittest.mock import MagicMock
import pytest
from pyclass_analyzer.types.result import ProjectPath
from pyclass_analyzer.collector.manager import CollectorManager

@pytest.fixture
def mock_file_collector():
    return MagicMock(
        collect=MagicMock(return_value=[
            ProjectPath(
                full_path="path/to/file.py",
                module_path="module.path",
                filename="file.py"
            )
        ])
    )

@pytest.fixture
def mock_package_collector():
    return MagicMock(
        collect=MagicMock(return_value=[
            "package1",
            "package2"
        ])
    )

@pytest.fixture
def mock_path():
    return "path/to/project"

class TestCollectorManager:
    def test_collect_success(self, mock_file_collector, mock_package_collector, mock_path):
        collector_manager = CollectorManager(mock_path)
        collector_manager._file_collector = mock_file_collector
        collector_manager._package_collector = mock_package_collector

        result = collector_manager.collect()

        assert result.packages == {"package1", "package2"}
        assert result.files == [ProjectPath(
            full_path="path/to/file.py",
            module_path="module.path",
            filename="file.py")]