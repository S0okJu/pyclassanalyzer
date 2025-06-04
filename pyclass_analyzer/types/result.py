from typing import List, Set

class ProjectPath:
    def __init__(self, full_path: str, module_path: str, filename: str):
        self.full_path = full_path
        self.module_path = module_path
        self.filename = filename

    def __str__(self):
        return f"{self.module_path}.{self.filename}"
    
    def __repr__(self):
        return f"ProjectPath(full_path={self.full_path}, module_path={self.module_path}, filename={self.filename})"
    
    def __eq__(self, other):
        if not isinstance(other, ProjectPath):
            return False
        return (self.full_path == other.full_path and 
                self.module_path == other.module_path and 
                self.filename == other.filename)
    
    def __hash__(self):
        return hash((self.full_path, self.module_path, self.filename))

class CollectorResult:
    def __init__(self):
        self.packages: Set[str] = set()
        self.files: List[ProjectPath] = list()
    
    def add(self, packages: Set[str], files: List[ProjectPath]):
        self.packages.update(packages)
        self.files.extend(files)
