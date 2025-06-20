import ast
from typing import Optional

from pyclassanalyzer.network.classgraph import (
    ClassGraph, ClassNode, Relation, RelationType, FunctionDef
)

class Visitor(ast.NodeVisitor):
    def __init__(self, graph:ClassGraph) -> None:
        self.graph = graph
        self.current_class: Optional[ClassNode] = None
        
        # 중복 방지용 
        self._composition_calls: set[int] = set()

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        class_ = ClassNode(name=node.name)
        self.graph.add_node(class_)
        self.current_class = class_
        
        # Decorator
        class_.annotations = [
            ast.unparse(dec) if hasattr(ast, "unparse") else "<decorator>"
            for dec in node.decorator_list
        ]
        
        # 상속 관계
        for base in node.bases:
            if isinstance(base, ast.Name):
                relation = Relation(
                    source= node.name,
                    target= base.id,
                    type_ = RelationType.INHERITANCE
                )
                self.graph.add_relation(relation)
        
        self.generic_visit(node)
        self.current_class = None
                
    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        if not self.current_class:
            return 
        
        func = FunctionDef(name=node.name)
        self.current_class.add_function(func=func)
        
        # USE
        for child in ast.walk(node):
            if isinstance(child, ast.Call) and \
                isinstance(child.func, ast.Name):
                
                if id(child) in self._composition_calls:
                    continue
                
                relation = Relation(
                    source= self.current_class.name,
                    target = child.func.id,
                    type_ = RelationType.USE
                )
                self.graph.add_relation(relation)
                
    # = 에 대응되는 
    # TODO: class 변수도 할지 
    def visit_Assign(self, node: ast.Assign) -> None:
        if self.current_class:
            for target in node.targets:
                # self.xxx 인경우에만 
                if isinstance(target, ast.Attribute) and \
                    isinstance(target, ast.Name) and \
                    target.value.id == 'self' :                    
                    
                    self.current_class.add_attribute(attr=target.attr)
                    
                    if isinstance(node.value, ast.Call) and \
                        isinstance(node.value.func, ast.Name):

                        class_name = node.value.func.id
                        relation = Relation(
                            source=self.current_class.name,
                            target=class_name,
                            type_=RelationType.COMPOSITION
                        )
                        
                        self.graph.add_relation(relation)                        
                        self._composition_calls.add(id(node.value))
                    
