import fnmatch
import ast
from typing import Optional, List

from pyclassanalyzer.network.classgraph import (
    ClassGraph, ClassNode, Relation, RelationType, FunctionDef, ClassType
)
from pyclassanalyzer.config import TomlConfig
from pyclassanalyzer.utils.class_type import is_magic


def check_exception_name(format:str, name:str) -> bool:
    """Check if the name matches the exception format.
    
    Args:
        format (str): The format of the exception name.
        name (str): The name to check.
        
    Returns:
        bool: True if the name matches the format, False otherwise.
    
    Example:
        check_exception_name('*Error', 'MyError') -> True
        check_exception_name('*Error', 'MyException') -> False
    """
    return bool(fnmatch.fnmatch(name, format))

class Visitor(ast.NodeVisitor):
    def __init__(self, graph:ClassGraph, config: TomlConfig) -> None:
        self.graph = graph
        self.current_class: Optional[ClassNode] = None
        
        # For avoiding duplication of composition relations
        self._composition_calls: set[int] = set()
        self._config = config
 

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Visit the class definition node.
        
        Args:
            node (ast.ClassDef): The class definition node.
        
        """
        
        # If "exception" is included in the [exclude] types in the TOML config,
        # and the name matches the required format,
        # skip processing the Visit class. 
        exception_format = self._config.get('exception')['name']
        exclude_exception = True if 'exception' in self._config.get('exclude')['types'] else False
        if exclude_exception and \
            check_exception_name(format=exception_format, name=node.name):
            return 
            
        # Create class node
        class_ = ClassNode(name=node.name)
        class_.annotations = self._parse_decorators(node.decorator_list)
        self._set_class_type(class_, exception_format)
        self._process_inheritance(class_, node.bases)
        
        self.graph.add_node(class_)
        self.current_class = class_

        # Traverse all nodes in the class
        self.generic_visit(node)
        self.current_class = None
    
    def _parse_decorators(self, decorator_list: list) -> List[str]:
        """Parse decorators from AST nodes to string representations.
        
        Args:
            decorator_list (list): The list of decorator nodes.
            
        Returns:
            List[str]: The list of decorator strings.
        """
        return [
            ast.unparse(dec) if hasattr(ast, "unparse") else "<decorator>"
            for dec in decorator_list
        ]
    
    def _set_class_type(self, class_: ClassNode, exception_format: str) -> None:
        """Set the class type based on decorators and name patterns.
        
        Args:
            class_ (ClassNode): The class node to set the type.
            exception_format (str): The format of the exception name.
        
        """
        # dataclass
        if 'dataclass' in class_.annotations:
            class_.type_ = ClassType.DATACLASS
            return
        
        # exception
        # If "exception" is included in the [exclude] types in the TOML config,
        # the name should be matched with the format.
        if check_exception_name(format=exception_format, name=class_.name):
            class_.type_ = ClassType.EXCEPTION
            return
    
    def _process_inheritance(self, class_: ClassNode, bases: list) -> None:
        """Process inheritance relationships and set special class types.
        
        Args:
            class_ (ClassNode): The class node to set the type.
            bases (list): The list of base nodes.
        
        NOTE:
        If the class type is already set, the specific class type is not set again.
        
        Special cases:
        - ABC -> ClassType.ABSTRACT
        - Enum -> ClassType.ENUM

        For example, if the class type is already set to ClassType.ENUM,
        the class type is not set to ClassType.ABSTRACT even if the base class is ABC.
        """
        for base in bases:
            if not isinstance(base, ast.Name):
                continue
                
            base_name = base.id
            
            # If the class type is already set, did not set the class type again.
            if class_.type_ == ClassType.CLASS:
                if base_name == 'Enum':
                    class_.type_ = ClassType.ENUM
                elif base_name == 'ABC':
                    class_.type_ = ClassType.ABSTRACT
            
            # Create inheritance relationship
            relation = Relation(
                source=class_.name,
                target=base_name,
                type_=RelationType.INHERITANCE
            )
            self.graph.add_relation(relation)
    
    # TODO: Track the object types of `self.xxx` attributes from method parameters.
    # For example, if `__init__(self, a:A): self.a = a`,
    # track the object type by mapping the parameter type `a:A` to the assignment `self.a = a` 
    def _parse_function_attrs(self, node: ast.FunctionDef) -> None:
        """Parse the method to identify dependency relationships 
        by analyzing the type hints of its attributes.
        
        Example:
            class Test:
                def __init__(self, a:A):
                    self.a = a
        
        It parses the type(A) from "__init__(self, a:A)" method. 
        
        Args:
            node (ast.FunctionDef): the node to parse
        """
        for arg in node.args.args:
            if arg.annotation and isinstance(arg.annotation, ast.Name):
                rel = Relation(
                    source=self.current_class.name,
                    target=arg.annotation.id,
                    type_=RelationType.DEPENDENCY
                )
                self.graph.add_relation(rel)
            
       
    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Visit the function definition node.
        
        Args:
            node (ast.FunctionDef): The function definition node.
            
        Example:
            This method handles the class functions:
            - def test_function(self, a:A):
        
        NOTE:
            In `__init__()`, this method handles the dependency relationships defined in the method parameters.
        """
        
        if not self.current_class:
            return

        func = FunctionDef(name=node.name)
        self.current_class.add_function(func=func)

        # NOTE: Focus only on dependency relationships defined in the '__init__()' method.
        # Marking all objects in method parameters can make the diagram complex.
        if func.name == '__init__':
            self._parse_function_attrs(node)
        
        # Traverse all nodes in the function
        for child in ast.walk(node):
            # set dependency relationship
            if isinstance(child, ast.Call) and isinstance(child.func, ast.Name):
                if id(child) in self._composition_calls:
                    continue
                
                relation = Relation(
                    source=self.current_class.name,
                    target=child.func.id,
                    type_=RelationType.DEPENDENCY
                )
                self.graph.add_relation(relation)

            # set composition relationship
            elif isinstance(child, ast.Assign):
                self._handle_function_assignment(child)

            # if the type annotation is assigned in the function,
            # set composition relationship
            elif isinstance(child, ast.AnnAssign):
                self._handle_function_annotated_assignment(child)

    def _handle_assignment(self, node: ast.Assign) -> None:
        """Handle assignment statements.
        
        Args:
            node (ast.Assign): The assignment node.
            
        Example:
            This method handles the class level attributes:
            - a = B()
            - self.xxx = B()
            - self.xxx: Type = B()
            
        """
        
        if not self.current_class:
            return

        for target in node.targets:
            
            # example: a = 1
            if isinstance(target, ast.Name):
                self.current_class.add_attribute(attr=target.id)

            # example: self.xxx = something
            elif isinstance(target, ast.Attribute) and \
               isinstance(target.value, ast.Name) and \
               target.value.id == 'self':

                self.current_class.add_attribute(attr=target.attr)

                # example: self.xxx = B()
                if isinstance(node.value, ast.Call):
                    func = node.value.func
                    class_name = None

                    if isinstance(func, ast.Name):
                        # example: self.attr = B()
                        class_name = func.id
                    elif isinstance(func, ast.Attribute):
                        # example: self.attr = module.B()
                        class_name = func.attr

                    if class_name and id(node.value) not in self._composition_calls:
                        relation = Relation(
                            source=self.current_class.name,
                            target=class_name,
                            type_=RelationType.COMPOSITION
                        )
                        self.graph.add_relation(relation)
                        self._composition_calls.add(id(node.value))

        # If the value is a call assignment, set the composition relationship.
        # not self.xxx assignment
        if isinstance(node.value, ast.Call):
            # self.xxx = Class() is already set in the above code.
            # skip this case
            is_self_assignment = any(
                isinstance(target, ast.Attribute) and 
                isinstance(target.value, ast.Name) and 
                target.value.id == 'self'
                for target in node.targets
            )
            # If the value is not self.xxx assignment, set the composition relationship.
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
        """Handle function assignment statements.
        
        Args:
            node (ast.Assign): The assignment node.
        """
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