import ast

from pyclassanalyzer.analyzer import MemberAnalyzer
from .base_visitor import BaseVisitor # Avoid circular import

class ClassVisitor(BaseVisitor):
    """Visitor class for class definition"""
    
    def __init__(self, result):
        super().__init__(result)
        self.member_analyzer = MemberAnalyzer(result)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Parse class definition
        
        They should use full name of the class to avoid duplicate class name. 
        (ex) hello.a vs world.a 
        """
        module_path = self.result.current_module
        class_name = f"{module_path}.{node.name}"
        self.result.class_modules[class_name] = module_path if module_path else ""
        simple_name = node.name
        if simple_name in self.result.class_name_to_full:
            existing_full = self.result.class_name_to_full[simple_name]
            print(f"Warning: Duplicate class name '{simple_name}' found. "
                  f"Existing: {existing_full}, New: {class_name}")
        self.result.class_name_to_full[simple_name] = class_name
        self._process_class_bases(node, class_name)
        
        # 클래스 멤버 분석
        self.current_class = class_name
        self.member_analyzer.analyze_class_members(node, class_name)
        
        # 조합 관계 분석
        self._analyze_composition(node, class_name)
        
        self.generic_visit(node)
        self.current_class = None

    def _process_class_bases(self, node: ast.ClassDef, class_name: str) -> None:
        """클래스의 상속 관계 처리 (full name만 사용, 디버깅 로그 추가)"""
        print(f"[DEBUG] class_name_to_full: {self.result.class_name_to_full}")
        bases = [self._get_base_name(base) for base in node.bases]
        for base in bases:
            base_full = self.result.class_name_to_full.get(base)
            if base_full and base_full in self.result.class_modules:
                print(f"[DEBUG] Adding inheritance: {class_name} <|-- {base_full}")
                self.result.inheritance[class_name].append(base_full)
            else:
                print(f"[WARNING] base class '{base}' not found as full name in class_modules, skipping relationship for {class_name}.")

    def _analyze_composition(self, node: ast.ClassDef, class_name: str) -> None:
        """클래스의 조합 관계 분석 (full name만 사용)"""
        for item in node.body:
            if isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name):
                        if isinstance(item.value, ast.Call):
                            if isinstance(item.value.func, ast.Name):
                                composed_class = item.value.func.id
                                composed_full = self.result.class_name_to_full.get(composed_class)
                                if composed_full and composed_full in self.result.class_modules:
                                    self.result.composition[class_name].add(composed_full)
                                else:
                                    print(f"[WARNING] composed class '{composed_class}' not found as full name in class_modules, skipping composition for {class_name}.")
            elif isinstance(item, ast.FunctionDef):
                if item.name == '__init__':
                    for stmt in ast.walk(item):
                        if isinstance(stmt, ast.Assign):
                            for target in stmt.targets:
                                if isinstance(target, ast.Attribute):
                                    if isinstance(target.value, ast.Name) and target.value.id == 'self':
                                        if isinstance(stmt.value, ast.Call):
                                            if isinstance(stmt.value.func, ast.Name):
                                                composed_class = stmt.value.func.id
                                                composed_full = self.result.class_name_to_full.get(composed_class)
                                                if composed_full and composed_full in self.result.class_modules:
                                                    self.result.composition[class_name].add(composed_full)
                                                else:
                                                    print(f"[WARNING] composed class '{composed_class}' not found as full name in class_modules, skipping composition for {class_name}.")

    def _get_base_name(self, base: ast.AST) -> str:
        """기본 클래스 이름 추출"""
        if isinstance(base, ast.Name):
            return base.id
        try:
            return ast.unparse(base)
        except Exception:
            return str(base)

    def _is_internal_import(self, imported_name: str) -> bool:
        """내부 import 여부 확인"""
        if '.' in imported_name:
            module_part = imported_name.rsplit('.', 1)[0]
            return self._is_internal_module(module_part)
        return self._is_internal_module(imported_name)

    def _is_internal_module(self, module_name: str) -> bool:
        """내부 모듈 여부 확인"""
        if not module_name:
            return True
        if module_name.startswith('.'):
            return True
        module_parts = module_name.split('.')
        if module_parts[0] in self.result.packages:
            return True
        if module_name in self.result.project_modules:
            return True
        return False 