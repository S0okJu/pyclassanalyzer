from pyclass_analyzer.collector.file import FileCollector
from pyclass_analyzer.collector.package import PackageCollector
from pyclass_analyzer.types.result import CollectorResult

class CollectorManager:
    """
    Collects files and packages from the project.
    - FileCollector: Collects files from the project.
    - PackageCollector: Collects packages from the project.
    - Result: A result class that contains the collected files and packages.
    """
    
    def __init__(self, path: str):
        self._file_collector = FileCollector(path)
        self._package_collector = PackageCollector(path)
        self.result = CollectorResult()

    def collect(self):
        """
        Collects files and packages from the project.

        Returns:
            CollectorResult: A result class that contains the collected files and packages.
        """
        files = self._file_collector.collect()
        packages = self._package_collector.collect()
        
        self.result.add(packages, files)
        return self.result