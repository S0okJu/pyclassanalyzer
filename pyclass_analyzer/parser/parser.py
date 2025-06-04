from typing import List
import ast

from pyclass_analyzer.visitor import Visitor
from pyclass_analyzer.types.result import CollectorResult

class ProjectParser:
    def __init__(self, result: CollectorResult):
        self.result = result
        
        self._visitor = Visitor(result=self.result)
        
    def parse(self):
        """
        Parse the project files and return the result.
        
        """
        
        for file in self.files:
            self.result.module_registry.add_module(file.module_path, file.filename)
            with open(file.full_path, 'r', encoding='utf-8') as f:
                try:
                    tree = ast.parse(f.read(), filename=file)
                    self._visitor.insert_current_module(file.module_path)
                    # 클래스 정의만 먼저 수집
                    for node in ast.walk(tree):
                        if isinstance(node, ast.ClassDef):
                            class_name = f"{file.module_path}.{node.name}"
                            self.result.class_registry.class_module[class_name] = file.module_path
                            self.result.class_registry.simple_to_full[node.name] = class_name
                except Exception as e:
                    print(f"Error in first pass for {file.full_path}: {e}")
                    continue
        
        for file in self.files:
            with open(file.full_path, 'r', encoding='utf-8') as f:
                try:
                    source = f.read()
                    tree = ast.parse(source, filename=file.full_path)
                    
                    self._visitor.insert_current_module(file.module_path)
                    self._visitor.visit(tree)
                    
                except Exception as e:
                    print(f"[ParseError] {file}: {e}")
        
        return self.result
