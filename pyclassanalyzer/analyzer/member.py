import ast
from typing import Dict, List, Any

from pyclassanalyzer.types import AnalysisResult


class MemberAnalyzer:
    """Analyze class members (attributes, methods)"""
    
    def __init__(self, result: AnalysisResult):
        self.result = result

    def analyze_class_members(self, node: ast.ClassDef, class_name: str) -> None:
        """Analyze class members"""
        attributes = {}
        methods = []
        
        for item in node.body:
            if isinstance(item, ast.Assign):
                self._process_class_attribute(item, attributes)
            elif isinstance(item, ast.FunctionDef):
                self._process_method(item, attributes, methods)
        
        self.result.class_attributes[class_name] = attributes
        self.result.class_methods[class_name] = methods

    def _process_class_attribute(self, node: ast.Assign, attributes: Dict[str, Any]) -> None:
        """Process class attribute"""
        for target in node.targets:
            if isinstance(target, ast.Name):
                attr_name = target.id
                attr_type = self._get_attribute_type(node.value)
                visibility = self._get_visibility(attr_name)
                attributes[attr_name] = {
                    'type': 'class_variable',
                    'data_type': attr_type,
                    'visibility': visibility,
                    'line': node.lineno
                }

    def _process_method(self, node: ast.FunctionDef, attributes: Dict[str, Any], methods: List[Dict[str, Any]]) -> None:
        """Process method"""
        method_name = node.name
        visibility = self._get_visibility(method_name)
        decorators = []
        is_property = False
        
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Name):
                dec_name = decorator.id
                decorators.append(dec_name)
                if dec_name == 'property':
                    is_property = True
            elif isinstance(decorator, ast.Attribute):
                if hasattr(decorator, 'attr'):
                    decorators.append(decorator.attr)
        
        method_info = {
            'name': method_name,
            'visibility': visibility,
            'decorators': decorators,
            'is_property': is_property,
            'line': node.lineno,
            'params': [arg.arg for arg in node.args.args[1:]]
        }
        methods.append(method_info)
        
        if is_property:
            attributes[method_name] = {
                'type': 'property',
                'data_type': 'property',
                'visibility': visibility,
                'line': node.lineno
            }
        
        if method_name == '__init__':
            self._analyze_init_method(node, attributes)
        else:
            dynamic_attrs = self._analyze_method_for_attributes(node)
            for attr_name, attr_info in dynamic_attrs.items():
                if attr_name not in attributes:
                    attributes[attr_name] = attr_info

    def _analyze_init_method(self, node: ast.FunctionDef, attributes: Dict[str, Any]) -> None:
        """Analyze __init__ method"""
        for stmt in ast.walk(node):
            if isinstance(stmt, ast.Assign):
                for target in stmt.targets:
                    if isinstance(target, ast.Attribute):
                        if isinstance(target.value, ast.Name) and target.value.id == 'self':
                            attr_name = target.attr
                            attr_type = self._get_attribute_type(stmt.value)
                            visibility = self._get_visibility(attr_name)
                            attributes[attr_name] = {
                                'type': 'instance_variable',
                                'data_type': attr_type,
                                'visibility': visibility,
                                'line': stmt.lineno
                            }

    def _analyze_method_for_attributes(self, method_node: ast.FunctionDef) -> Dict[str, Any]:
        """Analyze attributes created dynamically in the method"""
        attributes = {}
        for stmt in ast.walk(method_node):
            if isinstance(stmt, ast.Assign):
                for target in stmt.targets:
                    if isinstance(target, ast.Attribute):
                        if isinstance(target.value, ast.Name) and target.value.id == 'self':
                            attr_name = target.attr
                            attr_type = self._get_attribute_type(stmt.value)
                            visibility = self._get_visibility(attr_name)
                            attributes[attr_name] = {
                                'type': 'dynamic_attribute',
                                'data_type': attr_type,
                                'visibility': visibility,
                                'line': stmt.lineno,
                                'method': method_node.name
                            }
        return attributes

    def _get_attribute_type(self, value_node: ast.AST) -> str:
        """Infer the type of the attribute"""
        if isinstance(value_node, ast.Constant):
            return type(value_node.value).__name__
        elif isinstance(value_node, ast.Str):  # Python < 3.8
            return 'str'
        elif isinstance(value_node, ast.Num):  # Python < 3.8
            return 'int' if isinstance(value_node.n, int) else 'float'
        elif isinstance(value_node, ast.List):
            return 'list'
        elif isinstance(value_node, ast.Dict):
            return 'dict'
        elif isinstance(value_node, ast.Set):
            return 'set'
        elif isinstance(value_node, ast.Tuple):
            return 'tuple'
        elif isinstance(value_node, ast.Call):
            if isinstance(value_node.func, ast.Name):
                return value_node.func.id
        return 'object'

    def _get_visibility(self, name: str) -> str:
        """Determine the visibility of the member"""
        if name.startswith('__') and not name.endswith('__'):
            return 'private'
        elif name.startswith('_'):
            return 'protected'
        return 'public' 
