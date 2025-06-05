import ast
from typing import Dict, Optional
from ..models.class_info import ClassInfo, AttributeInfo, MethodInfo
from ..models.module_info import ModuleInfo

class ASTVisitor(ast.NodeVisitor):
    def __init__(self, module_info: ModuleInfo):
        self.module_info = module_info
        self.current_class: Optional[ClassInfo] = None
        self.classes: Dict[str, ClassInfo] = {}
        self.project_analyzer = None  # Will be set by ClassAnalyzer

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            module_name = alias.name
            alias_name = alias.asname if alias.asname else alias.name
            self.module_info.add_import(alias_name, module_name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        if node.module:
            for alias in node.names:
                imported_name = alias.name
                alias_name = alias.asname if alias.asname else imported_name
                full_name = f"{node.module}.{imported_name}"
                self.module_info.add_import(alias_name, full_name)
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef):
        class_name = f"{self.module_info.name}.{node.name}" if self.module_info.name else node.name
        class_info = ClassInfo(name=class_name, module=self.module_info.name)
        self.module_info.add_class(class_name)
        self.classes[class_name] = class_info
        self.current_class = class_info

        # Analyze bases
        for base in node.bases:
            base_name = self._get_base_name(base)
            # Try to resolve to full name if imported
            imported_full = self.module_info.imports.get(base_name, base_name)
            # Internal/external check
            is_internal = self.project_analyzer and self.project_analyzer.is_internal_module(imported_full)
            class_info.add_base(imported_full)
            if not is_internal:
                # Mark as external
                if imported_full not in self.classes:
                    base_info = ClassInfo(name=imported_full, module=imported_full.split('.')[0])
                    base_info.is_external = True
                    self.classes[imported_full] = base_info

        self._analyze_class_members(node)
        self.generic_visit(node)
        self.current_class = None

    def visit_Assign(self, node: ast.Assign):
        if not self.current_class:
            return
        # self.xxx = SomeClass()
        if isinstance(node.targets[0], ast.Attribute):
            attr = node.targets[0]
            if isinstance(attr.value, ast.Name) and attr.value.id == 'self':
                if isinstance(node.value, ast.Call):
                    if isinstance(node.value.func, ast.Name):
                        member_class = node.value.func.id
                        imported_full = self.module_info.imports.get(member_class, member_class)
                        is_internal = self.project_analyzer and self.project_analyzer.is_internal_module(imported_full)
                        self.current_class.add_composition(imported_full)
                        if not is_internal:
                            if imported_full not in self.classes:
                                class_info = ClassInfo(name=imported_full, module=imported_full.split('.')[0])
                                class_info.is_external = True
                                self.classes[imported_full] = class_info
        self.generic_visit(node)

    def _analyze_class_members(self, node: ast.ClassDef):
        for item in node.body:
            if isinstance(item, ast.Assign):
                self._analyze_class_attribute(item)
            elif isinstance(item, ast.FunctionDef):
                self._analyze_method(item)

    def _analyze_class_attribute(self, node: ast.Assign):
        if not self.current_class:
            return
        for target in node.targets:
            if isinstance(target, ast.Name):
                attr_info = AttributeInfo(
                    name=target.id,
                    type='class_variable',
                    data_type=self._get_attribute_type(node.value),
                    visibility=self._get_visibility(target.id),
                    line=node.lineno
                )
                self.current_class.add_attribute(attr_info)

    def _analyze_method(self, node: ast.FunctionDef):
        if not self.current_class:
            return
        decorators = []
        is_property = False
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Name):
                decorators.append(decorator.id)
                if decorator.id == 'property':
                    is_property = True
            elif isinstance(decorator, ast.Attribute):
                if hasattr(decorator, 'attr'):
                    decorators.append(decorator.attr)
        method_info = MethodInfo(
            name=node.name,
            visibility=self._get_visibility(node.name),
            decorators=decorators,
            is_property=is_property,
            line=node.lineno,
            params=[arg.arg for arg in node.args.args[1:]]  # Skip self
        )
        self.current_class.add_method(method_info)
        if is_property:
            attr_info = AttributeInfo(
                name=node.name,
                type='property',
                data_type='property',
                visibility=method_info.visibility,
                line=node.lineno
            )
            self.current_class.add_attribute(attr_info)
        if node.name == '__init__':
            self._analyze_init_method(node)

    def _analyze_init_method(self, node: ast.FunctionDef):
        for stmt in ast.walk(node):
            if isinstance(stmt, ast.Assign):
                for target in stmt.targets:
                    if isinstance(target, ast.Attribute):
                        if isinstance(target.value, ast.Name) and target.value.id == 'self':
                            attr_info = AttributeInfo(
                                name=target.attr,
                                type='instance_variable',
                                data_type=self._get_attribute_type(stmt.value),
                                visibility=self._get_visibility(target.attr),
                                line=stmt.lineno
                            )
                            self.current_class.add_attribute(attr_info)

    def _get_attribute_type(self, value_node: ast.AST) -> str:
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
        if name.startswith('__') and not name.endswith('__'):
            return 'private'
        elif name.startswith('_'):
            return 'protected'
        return 'public'

    def _get_base_name(self, base: ast.AST) -> str:
        if isinstance(base, ast.Name):
            return base.id
        try:
            return ast.unparse(base)
        except Exception:
            return str(base) 