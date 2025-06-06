import ast
from typing import Optional
from dataclasses import dataclass, field
from ..models.analysis_context import AnalysisContext

@dataclass
class BaseVisitor(ast.NodeVisitor):
    """기본 AST 방문자 클래스"""
    context: AnalysisContext
    current_class: Optional[str] = None
    current_module: Optional[str] = None

    def __init__(self, context: AnalysisContext):
        super().__init__()
        self.context = context

    def visit_Module(self, node: ast.Module) -> None:
        """모듈 방문"""
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """클래스 정의 방문"""
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """함수 정의 방문"""
        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign) -> None:
        """할당문 방문"""
        self.generic_visit(node) 