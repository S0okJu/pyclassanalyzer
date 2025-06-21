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
        if not self.current_class:
            return
    
        for target in node.targets:
            if isinstance(target, ast.Attribute) and \
               isinstance(target.value, ast.Name) and \
               target.value.id == 'self':
                
                # 예: self.xxx
                self.current_class.add_attribute(attr=target.attr)
    
                # 예: self.xxx = B() or self.xxx = module.B()
                if isinstance(node.value, ast.Call):
                    func = node.value.func
                    class_name = None
    
                    if isinstance(func, ast.Name):
                        # B()
                        class_name = func.id
                    elif isinstance(func, ast.Attribute):
                        # module.B()
                        class_name = func.attr
    
                    if class_name and id(node.value) not in self._composition_calls:
                        relation = Relation(
                            source=self.current_class.name,
                            target=class_name,
                            type_=RelationType.COMPOSITION
                        )
                        self.graph.add_relation(relation)
                        self._composition_calls.add(id(node.value))
                        
    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        if not self.current_class:
            return
        
        attr = None
        if isinstance(node.target, ast.Name):
            attr = node.target.id
        elif isinstance(node.target, ast.Attribute) and \
            isinstance(node.target.value, ast.Name) and \
            node.target.value.id == 'self':
            attr = node.target.attr
        
        if not attr:
            return 
        
        self.current_class.add_attribute(attr=attr)
        
        # Composition
        
        type_classes = extract_type_names(node.annotation)
        for class_ in type_classes: 
            if class_ in ('str','int','float', 'bool','Any'):
                continue
            
            
            relation = Relation(
                source=self.current_class.name,
                target=class_,
                type_=RelationType.COMPOSITION
            )
            self.graph.add_relation(relation=relation)
            

def extract_type_names(annotation: ast.AST) -> set[str]:
    """
    주어진 annotation AST 노드에서 클래스 이름을 추출한다.
    예: Optional[Address], List[User], Dict[str, MyModel] 등
    """
    type_names = set()

    if isinstance(annotation, ast.Name):
        # 기본 타입: Address
        type_names.add(annotation.id)

    elif isinstance(annotation, ast.Attribute):
        # 모듈 속 타입: typing.Optional → Optional
        type_names.add(annotation.attr)

    elif isinstance(annotation, ast.Subscript):
        # 예: Optional[Address], List[User], Dict[str, Address]
        # 원소 추가
        type_names |= extract_type_names(annotation.slice)
        type_names |= extract_type_names(annotation.value)

    elif isinstance(annotation, ast.Tuple):
        # 예: Union[A, B] → slice가 Tuple일 수 있음
        for elt in annotation.elts:
            type_names |= extract_type_names(elt)

    elif isinstance(annotation, ast.Index):  # Python < 3.9
        type_names |= extract_type_names(annotation.value)

    return type_names