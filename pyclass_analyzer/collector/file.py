import os
from typing import List

from pyclass_analyzer.collector.collector import Collector
from pyclass_analyzer.types.result import ProjectPath

class FileCollector(Collector):
    def __init__(self, path: str):
        """
        Initialize the FileCollector with a root path.
        
        Args:
            path (str): The directory path to search for Python files.
        """
        self.path = path

    def _convert_module_path(self, full_path: str) -> str:
        """
        Convert a full file path to a Python module path.

        Args:
            full_path (str): The absolute file path.

        Returns:
            str: A dotted module path (e.g., 'package.module').
        """
        
        rel_path = os.path.relpath(full_path, self.path)
        return os.path.splitext(rel_path)[0].replace(os.path.sep, ".")

    def collect(self) -> List[ProjectPath]:
        """
        Collect all Python module paths in the given path.

        Returns:
            List[ProjectPath]: A list of module paths 
        """
        files = []
        for root, _, file_names in os.walk(self.path):
            for filename in file_names:
                if filename.endswith('.py') and filename != '__init__.py':
                    full_path = os.path.join(root, filename)
                    module_path = self._convert_module_path(full_path)
                    files.append(ProjectPath(full_path, module_path, filename))
        return files
