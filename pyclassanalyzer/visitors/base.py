import ast
from typing import Optional
from dataclasses import dataclass
from pyclassanalyzer.types import AnalysisResult

@dataclass
class BaseVisitor(ast.NodeVisitor):
    """Base visitor class for AST
    
    This class is a base class for all the visitors.
    All the class methods override the methods of the ast.NodeVisitor class named as visit_{object_name}.
    (ex) visit_ClassDef, visit_FunctionDef, visit_Assign, etc.
    """
    result: AnalysisResult
    current_class: Optional[str] = None
    current_module: Optional[str] = None

    def __init__(self, result: AnalysisResult):
        super().__init__()
        self.result = result

    def visit_Module(self, node: ast.Module) -> None:
        """Visit module"""
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Visit class definition"""
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Visit function definition"""
        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign) -> None:
        """Visit assignment"""
        self.generic_visit(node) 