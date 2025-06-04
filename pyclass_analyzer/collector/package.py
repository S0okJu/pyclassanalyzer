import os

from pyclass_analyzer.collector.collector import Collector

class PackageCollector(Collector):
    """
    Collects packages from the project.
    - General package: packages in the project
    - Top package: the root package of the project
    """
    
    def __init__(self, path: str):
        super().__init__(path)
        self._packages = set()

    def _collect_general_package(self):
        """
        Collects general packages from the project.
        - General package: packages in the project
        
        !NOTICE: This method should have __init__.py method.
        """
        for root, _ , files in os.walk(self.path):
            if '__init__.py' in files:
                rel_path = os.path.relpath(root, self.path)
                pkg = rel_path.replace(os.path.sep, ".") if rel_path != '.' else ''
                
                if pkg:
                    self._packages.add(pkg)
        
    def _collect_top_package(self):
        """
        Collects top packages from the project.
        - Top package: the root package of the project
        
        This is used for showing the project structure in the diagram.
        """
        project_root_name = os.path.basename(os.path.abspath(self.path))
        if project_root_name and project_root_name != '.':
            self._packages.add(project_root_name) 
    
    def collect(self):
        self._collect_general_package()
        self._collect_top_package()
        
        return self._packages