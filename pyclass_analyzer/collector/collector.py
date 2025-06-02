import os

class FileCollector:
    def __init__(self, path):
        self.path = path

    def collect(self):
        files = []
        for root, _, file_names in os.walk(self.path):
            for file in file_names:
                if file.endswith('.py') and file != '__init__.py':
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, self.path)
                    module_path = os.path.splitext(rel_path)[0].replace(os.path.sep, ".")
                    files.append((full_path, module_path, file))
        return files