import os 
import ast
from collections import defaultdict
from result import Result

class DirectoryAnalyzer:
    def __init__(self, path):
        self._path = path
        self._result = Result()

    
    def _collect_project_structure(self):
        """프로젝트 구조 수집"""
        # 패키지 정보 수집
        for root, dirs, files in os.walk(self._path):
            if '__init__.py' in files:
                rel_path = os.path.relpath(root, self._path)
                pkg = rel_path.replace(os.path.sep, ".") if rel_path != '.' else ''
                if pkg:
                    self._result.add_package(pkg)
        
        # 최상위 디렉토리명도 패키지로 간주 (일반적인 프로젝트 구조)
        project_root_name = os.path.basename(os.path.abspath(self._path))
        if project_root_name and project_root_name != '.':
            self._result.add_package(project_root_name)
    
    def _collect_classes(self):

        # 2단계: 모든 파일을 먼저 순회해서 클래스 정보 수집
        all_files = []
        for root, _, files in os.walk(self._path):
            for file in files:
                if file.endswith('.py') and file != '__init__.py':
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, self._path)
                    module_path_without_ext = os.path.splitext(rel_path)[0]
                    module_path = module_path_without_ext.replace(os.path.sep, ".")
                    all_files.append((full_path, module_path, file))
        
        # 3단계: 첫 번째 패스 - 클래스 정의만 수집
        for full_path, module_path, file in all_files:
            self._result.module_to_file[module_path] = file
            self._result.project_modules.add(module_path)
            
            with open(full_path, 'r', encoding='utf-8') as f:
                try:
                    tree = ast.parse(f.read(), filename=file)
                    self._result.current_module = module_path
                    # 클래스 정의만 먼저 수집
                    for node in ast.walk(tree):
                        if isinstance(node, ast.ClassDef):
                            class_name = f"{module_path}.{node.name}"
                            self._result.class_modules[class_name] = module_path
                            self._result.class_name_to_full[node.name] = class_name
                except Exception as e:
                    print(f"Error in first pass for {full_path}: {e}")
                    continue
    
        for full_path, module_path, file in all_files:
            with open(full_path, 'r', encoding='utf-8') as f:
                try:
                    tree = ast.parse(f.read(), filename=file)
                    self._result.current_module = module_path
                    self._result.visit(tree)
                except Exception as e:
                    print(f"Error in second pass for {full_path}: {e}")
                    continue
        self._result.current_module = None
        
    def analyze(self):
        self._collect_project_structure()
        self._collect_classes()
        
    