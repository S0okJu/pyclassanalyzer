import ast
from .base_visitor import BaseVisitor

class ImportVisitor(BaseVisitor):
    """import 문을 처리하는 방문자 클래스"""
    
    def visit_Import(self, node: ast.Import) -> None:
        """import 문 처리"""
        for alias in node.names:
            module_name = alias.name
            alias_name = alias.asname if alias.asname else alias.name
            self.context.imports[self.current_module][alias_name] = module_name
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """from ... import 문 처리"""
        if node.module:
            for alias in node.names:
                imported_name = alias.name
                alias_name = alias.asname if alias.asname else imported_name
                full_name = f"{node.module}.{imported_name}"
                self.context.imports[self.current_module][alias_name] = full_name
                if not self._is_internal_module(node.module):
                    self.context.external_classes.add(alias_name)
        self.generic_visit(node)

    def _is_internal_module(self, module_name: str) -> bool:
        """내부 모듈 여부 확인"""
        if not module_name:
            return True
        if module_name.startswith('.'):
            return True
        module_parts = module_name.split('.')
        if module_parts[0] in self.context.packages:
            return True
        if module_name in self.context.project_modules:
            return True
        return False 