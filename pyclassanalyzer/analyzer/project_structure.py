import os

class ProjectStructureAnalyzer:
    def __init__(self):
        self.packages = set()
        self.modules = set()
        self.project_root = ""

    def analyze(self, path: str):
        self.project_root = os.path.abspath(path)
        self._collect_project_structure(path)
        return self.modules

    def _collect_project_structure(self, path):
        for root, dirs, files in os.walk(path):
            if '__init__.py' in files:
                rel_path = os.path.relpath(root, path)
                pkg = rel_path.replace(os.path.sep, ".") if rel_path != '.' else ''
                if pkg:
                    self.packages.add(pkg)
        project_root_name = os.path.basename(os.path.abspath(path))
        if project_root_name and project_root_name != '.':
            self.packages.add(project_root_name)
        for root, _, files in os.walk(path):
            for file in files:
                if file.endswith('.py') and file != '__init__.py':
                    rel_path = os.path.relpath(os.path.join(root, file), path)
                    module_path = os.path.splitext(rel_path)[0].replace(os.path.sep, ".")
                    self.modules.add(module_path) 