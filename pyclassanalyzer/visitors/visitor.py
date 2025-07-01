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
        
        # Decorator
        class_.annotations = [
            ast.unparse(dec) if hasattr(ast, "unparse") else "<decorator>"
            for dec in node.decorator_list
        ]
        
        self.graph.add_node(class_)
        self.current_class = class_
        
        # 상속 관계
        for base in node.bases:
            if isinstance(base, ast.Name):
                # Enum, ABC 타입 처리
                if base.id == 'Enum':
                    class_.set_enum()
                elif base.id == 'ABC':
                    class_.set_abstract()
                else:
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

        # 함수 내부의 모든 노드를 순회
        for child in ast.walk(node):
            # USE 관계 처리
            if isinstance(child, ast.Call) and isinstance(child.func, ast.Name):
                if id(child) in self._composition_calls:
                    continue
                
                relation = Relation(
                    source=self.current_class.name,
                    target=child.func.id,
                    type_=RelationType.USE
                )
                self.graph.add_relation(relation)

            # 함수 내부의 할당문에서 composition 관계만 처리
            elif isinstance(child, ast.Assign):
                self._handle_function_assignment(child)

            # 함수 내부의 타입 어노테이션 할당에서 composition 관계만 처리
            elif isinstance(child, ast.AnnAssign):
                self._handle_function_annotated_assignment(child)

    def _handle_assignment(self, node: ast.Assign) -> None:
        """할당문 처리 로직을 분리한 헬퍼 메서드"""
        if not self.current_class:
            return

        for target in node.targets:
            # a = 1
            if isinstance(target, ast.Name):
                self.current_class.add_attribute(attr=target.id)

            # self.xxx = something
            elif isinstance(target, ast.Attribute) and \
               isinstance(target.value, ast.Name) and \
               target.value.id == 'self':

                self.current_class.add_attribute(attr=target.attr)

                if isinstance(node.value, ast.Call):
                    func = node.value.func
                    class_name = None

                    if isinstance(func, ast.Name):
                        # self.attr = B()
                        class_name = func.id
                    elif isinstance(func, ast.Attribute):
                        # self.attr = module.B()
                        class_name = func.attr

                    if class_name and id(node.value) not in self._composition_calls:
                        relation = Relation(
                            source=self.current_class.name,
                            target=class_name,
                            type_=RelationType.COMPOSITION
                        )
                        self.graph.add_relation(relation)
                        self._composition_calls.add(id(node.value))

        # 일반 변수 할당에서의 composition 체크 (self.xxx가 아닌 경우)
        if isinstance(node.value, ast.Call):
            # self.xxx = SomeClass() 케이스는 이미 위에서 처리했으므로 제외
            is_self_assignment = any(
                isinstance(target, ast.Attribute) and 
                isinstance(target.value, ast.Name) and 
                target.value.id == 'self'
                for target in node.targets
            )

            if not is_self_assignment:
                func = node.value.func
                class_name = None

                if isinstance(func, ast.Name):
                    # temp = B()
                    class_name = func.id
                elif isinstance(func, ast.Attribute):
                    # temp = module.B()
                    class_name = func.attr

                if class_name and id(node.value) not in self._composition_calls:
                    relation = Relation(
                        source=self.current_class.name,
                        target=class_name,
                        type_=RelationType.COMPOSITION
                    )
                    self.graph.add_relation(relation)
                    self._composition_calls.add(id(node.value))

    def _handle_function_assignment(self, node: ast.Assign) -> None:
        """함수 내부 할당문에서 composition 관계만 처리 (속성 추가 안함)"""
        if not self.current_class:
            return

        for target in node.targets:
            # self.xxx = something만 속성으로 추가
            if isinstance(target, ast.Attribute) and \
               isinstance(target.value, ast.Name) and \
               target.value.id == 'self':

                self.current_class.add_attribute(attr=target.attr)

                if isinstance(node.value, ast.Call):
                    func = node.value.func
                    class_name = None

                    if isinstance(func, ast.Name):
                        class_name = func.id
                    elif isinstance(func, ast.Attribute):
                        class_name = func.attr

                    if class_name and id(node.value) not in self._composition_calls:
                        relation = Relation(
                            source=self.current_class.name,
                            target=class_name,
                            type_=RelationType.COMPOSITION
                        )
                        self.graph.add_relation(relation)
                        self._composition_calls.add(id(node.value))

    def _handle_function_annotated_assignment(self, node: ast.AnnAssign) -> None:
        """함수 내부 타입 어노테이션 할당에서 composition 관계만 처리"""
        if not self.current_class:
            return

        # self.xxx: Type = ... 만 속성으로 추가
        if isinstance(node.target, ast.Attribute) and \
            isinstance(node.target.value, ast.Name) and \
            node.target.value.id == 'self':

            attr = node.target.attr
            self.current_class.add_attribute(attr=attr)

            # Composition 관계 추가
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

    def visit_Assign(self, node: ast.Assign) -> None:
        """클래스 레벨 할당문 처리"""
        self._handle_assignment(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        """클래스 레벨 타입 어노테이션 할당문 처리"""
        if not self.current_class:
            return

        # 클래스 레벨에서는 모든 변수가 속성
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