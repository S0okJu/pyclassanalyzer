import ast
import os
from collections import defaultdict
from typing import Dict

from ..models.class_info import ClassInfo
from ..models.module_info import ModuleInfo
from .ast_visitor import ASTVisitor
from .project_structure import ProjectStructureAnalyzer
from ..utils.plantuml_formatter import PlantUMLFormatter

class ClassAnalyzer(ast.NodeVisitor):
    def __init__(self):
        self.inheritance = defaultdict(list)
        self.composition = defaultdict(set)
        self.class_modules = {}
        self.class_name_to_full = {}
        self.current_class = None
        self.current_module = None
        self.packages = set()
        self.external_classes = set()
        self.module_to_file = {}
        self.imports = defaultdict(dict)
        self.project_modules = set()
        self.class_attributes = defaultdict(dict)
        self.class_methods = defaultdict(list)
        self.project_analyzer = ProjectStructureAnalyzer()
        self.classes: Dict[str, ClassInfo] = {}

    def visit_Import(self, node):
        for alias in node.names:
            module_name = alias.name
            alias_name = alias.asname if alias.asname else alias.name
            self.imports[self.current_module][alias_name] = module_name
            if not self._is_internal_module(module_name):
                pass

    def visit_ImportFrom(self, node):
        if node.module:
            for alias in node.names:
                imported_name = alias.name
                alias_name = alias.asname if alias.asname else alias.name
                full_name = f"{node.module}.{imported_name}"
                self.imports[self.current_module][alias_name] = full_name
                if not self._is_internal_module(node.module):
                    self.external_classes.add(alias_name)

    def _is_internal_module(self, module_name):
        if not module_name:
            return True
        if module_name.startswith('.'):
            return True
        module_parts = module_name.split('.')
        if module_parts[0] in self.packages:
            return True
        if module_name in self.project_modules:
            return True
        return False

    def visit_ClassDef(self, node):
        class_name = f"{self.current_module}.{node.name}" if self.current_module else node.name
        self.class_modules[class_name] = self.current_module if self.current_module else ""
        simple_name = node.name
        if simple_name in self.class_name_to_full:
            existing_full = self.class_name_to_full[simple_name]
            print(f"Warning: Duplicate class name '{simple_name}' found. "
                  f"Existing: {existing_full}, New: {class_name}")
        self.class_name_to_full[simple_name] = class_name
        bases = [self.get_base_name(base) for base in node.bases]
        for base in bases:
            if base in self.imports.get(self.current_module, {}):
                imported_full_name = self.imports[self.current_module][base]
                if not self._is_internal_import(imported_full_name):
                    self.external_classes.add(base)
                    self.inheritance[class_name].append(base)
                else:
                    base_full = self.class_name_to_full.get(base, base)
                    self.inheritance[class_name].append(base_full)
            else:
                base_full = self.class_name_to_full.get(base, base)
                if base_full in self.class_modules:
                    self.inheritance[class_name].append(base_full)
                elif base in self.class_name_to_full:
                    self.inheritance[class_name].append(self.class_name_to_full[base])
                else:
                    self.external_classes.add(base)
                    self.inheritance[class_name].append(base)
        self.current_class = class_name
        self._analyze_class_members(node, class_name)
        self.generic_visit(node)
        self.current_class = None

    def _analyze_class_members(self, node, class_name):
        attributes = {}
        methods = []
        for item in node.body:
            if isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name):
                        attr_name = target.id
                        attr_type = self._get_attribute_type(item.value)
                        visibility = self._get_visibility(attr_name)
                        attributes[attr_name] = {
                            'type': 'class_variable',
                            'data_type': attr_type,
                            'visibility': visibility,
                            'line': item.lineno
                        }
            elif isinstance(item, ast.FunctionDef):
                method_name = item.name
                visibility = self._get_visibility(method_name)
                decorators = []
                is_property = False
                for decorator in item.decorator_list:
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
                    'line': item.lineno,
                    'params': [arg.arg for arg in item.args.args[1:]]
                }
                methods.append(method_info)
                if is_property:
                    attributes[method_name] = {
                        'type': 'property',
                        'data_type': 'property',
                        'visibility': visibility,
                        'line': item.lineno
                    }
                if method_name == '__init__':
                    instance_attrs = self._analyze_init_method(item)
                    attributes.update(instance_attrs)
                else:
                    dynamic_attrs = self._analyze_method_for_attributes(item)
                    for attr_name, attr_info in dynamic_attrs.items():
                        if attr_name not in attributes:
                            attributes[attr_name] = attr_info
        self.class_attributes[class_name] = attributes
        self.class_methods[class_name] = methods

    def _analyze_init_method(self, init_node):
        attributes = {}
        for stmt in ast.walk(init_node):
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
        return attributes

    def _analyze_method_for_attributes(self, method_node):
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

    def _get_attribute_type(self, value_node):
        if isinstance(value_node, ast.Constant):
            return type(value_node.value).__name__
        elif isinstance(value_node, ast.Str):
            return 'str'
        elif isinstance(value_node, ast.Num):
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
            else:
                return 'object'
        else:
            return 'object'

    def _get_visibility(self, name):
        if name.startswith('__') and not name.endswith('__'):
            return 'private'
        elif name.startswith('_'):
            return 'protected'
        else:
            return 'public'

    def _is_internal_import(self, imported_name):
        if '.' in imported_name:
            module_part = imported_name.rsplit('.', 1)[0]
            return self._is_internal_module(module_part)
        return self._is_internal_module(imported_name)

    def visit_Assign(self, node):
        if isinstance(node.targets[0], ast.Attribute):
            attr = node.targets[0]
            if isinstance(attr.value, ast.Name) and attr.value.id == 'self':
                if isinstance(node.value, ast.Call):
                    if isinstance(node.value.func, ast.Name):
                        member_class_short = node.value.func.id
                        if self.current_class:
                            if member_class_short in self.imports.get(self.current_module, {}):
                                imported_full_name = self.imports[self.current_module][member_class_short]
                                if not self._is_internal_import(imported_full_name):
                                    self.external_classes.add(member_class_short)
                                else:
                                    member_class = self.class_name_to_full.get(member_class_short, member_class_short)
                                    self.composition[self.current_class].add(member_class)
                            elif member_class_short in self.class_name_to_full:
                                member_class = self.class_name_to_full[member_class_short]
                                self.composition[self.current_class].add(member_class)
                            else:
                                self.external_classes.add(member_class_short)
        self.generic_visit(node)

    def get_base_name(self, base):
        if isinstance(base, ast.Name):
            return base.id
        try:
            return ast.unparse(base)
        except Exception:
            return str(base)

    def analyze_directory(self, path):
        self._collect_project_structure(path)
        all_files = []
        for root, _, files in os.walk(path):
            for file in files:
                if file.endswith('.py') and file != '__init__.py':
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, path)
                    module_path_without_ext = os.path.splitext(rel_path)[0]
                    module_path = module_path_without_ext.replace(os.path.sep, ".")
                    all_files.append((full_path, module_path, file))
        for full_path, module_path, file in all_files:
            self.module_to_file[module_path] = file
            self.project_modules.add(module_path)
            with open(full_path, 'r', encoding='utf-8') as f:
                try:
                    tree = ast.parse(f.read(), filename=file)
                    self.current_module = module_path
                    for node in ast.walk(tree):
                        if isinstance(node, ast.ClassDef):
                            class_name = f"{module_path}.{node.name}"
                            self.class_modules[class_name] = module_path
                            self.class_name_to_full[node.name] = class_name
                except Exception as e:
                    print(f"Error in first pass for {full_path}: {e}")
                    continue
        for full_path, module_path, file in all_files:
            with open(full_path, 'r', encoding='utf-8') as f:
                try:
                    tree = ast.parse(f.read(), filename=file)
                    self.current_module = module_path
                    self.visit(tree)
                except Exception as e:
                    print(f"Error in second pass for {full_path}: {e}")
                    continue
        self.current_module = None

    def _collect_project_structure(self, path):
        for root, dirs, files in os.walk(path):
            if '__init__.py' in files:
                rel_path = os.path.relpath(root, path)
                pkg = rel_path.replace(os.path.sep, ".") if rel_path != '.' else ''
                if pkg:
                    self.packages.add(pkg)
        project_root_name = os.path.basename(os.path.abspath(path))
        if project_root_name and project_root_name != '.':
            self.packages.add(project_root_name)

    def _format_attribute_for_plantuml(self, attr_name, attr_info):
        visibility_symbol = {
            'public': '+',
            'protected': '#',
            'private': '-'
        }
        symbol = visibility_symbol.get(attr_info['visibility'], '+')
        data_type = attr_info.get('data_type', 'object')
        if data_type in ['int', 'str', 'float', 'bool', 'list', 'dict', 'set', 'tuple']:
            type_str = f": {data_type}"
        elif data_type == 'property':
            type_str = " {property}"
        else:
            type_str = f": {data_type}" if data_type != 'object' else ""
        return f"{symbol}{attr_name}{type_str}"

    def _format_method_for_plantuml(self, method_info):
        visibility_symbol = {
            'public': '+',
            'protected': '#',
            'private': '-'
        }
        symbol = visibility_symbol.get(method_info['visibility'], '+')
        method_name = method_info['name']
        if method_name in ['__init__', '__str__', '__repr__']:
            return f"{symbol}{method_name}()"
        if method_info.get('is_property', False):
            return None
        params = method_info.get('params', [])
        if len(params) <= 2:
            param_str = ', '.join(params)
        else:
            param_str = f"{params[0]}, ..."
        param_part = f"({param_str})" if param_str else "()"
        decorators = method_info.get('decorators', [])
        decorator_str = ""
        if decorators:
            if 'staticmethod' in decorators:
                decorator_str = " {static}"
            elif 'classmethod' in decorators:
                decorator_str = " {class}"
        return f"{symbol}{method_name}{param_part}{decorator_str}"

    def save_plantuml_diagram(self, filename="class_diagram.puml", include_attributes=True, include_methods=True):
        modules = defaultdict(list)
        for cls, mod in self.class_modules.items():
            modules[mod].append(cls)
        tree = {}
        for mod, classes in modules.items():
            if not mod:
                continue
            parts = mod.split('.')
            current_node = tree
            for i in range(len(parts) - 1):
                package_name = parts[i]
                if package_name not in current_node:
                    current_node[package_name] = {}
                current_node = current_node[package_name]
            if '_files' not in current_node:
                current_node['_files'] = []
            current_node['_files'].append(mod)
        def sanitize(name):
            return "".join(c if c.isalnum() else "_" for c in name)
        with open(filename, "w", encoding="utf-8") as f:
            f.write("@startuml\n\n")
            f.write('skinparam class {\n')
            f.write('  BackgroundColor<<External>> LightBlue\n')
            f.write('}\n\n')
            declared_classes = set()
            declared_relationships = set()
            def declare_class(cls_name, external=False):
                cls_id = sanitize(cls_name)
                if cls_id not in declared_classes:
                    declared_classes.add(cls_id)
                    simple_name = cls_name.split(".")[-1]
                    if external:
                        f.write(f'class {cls_id} as "{simple_name}" <<External>>\n')
                    else:
                        f.write(f'class {cls_id} as "{simple_name}"\n')
                return cls_id
            def write_tree(node, indent=0):
                indent_str = "  " * indent
                if '_files' in node:
                    for mod in node['_files']:
                        if mod in self.module_to_file:
                            file_name = self.module_to_file[mod]
                            file_name_without_ext = os.path.splitext(file_name)[0]
                        else:
                            module_parts = mod.split('.')
                            file_name_without_ext = module_parts[-1]
                        escaped_file_name = f'"{file_name_without_ext}"' if '.' in file_name_without_ext else file_name_without_ext
                        f.write(f'{indent_str}frame {escaped_file_name} {{\n')
                        for cls in modules.get(mod, []):
                            cls_id = sanitize(cls)
                            simple_name = cls.split(".")[-1]
                            f.write(f'{indent_str}  class {cls_id} as "{simple_name}" {{\n')
                            if include_attributes and cls in self.class_attributes:
                                attributes = self.class_attributes[cls]
                                if attributes:
                                    for attr_name, attr_info in attributes.items():
                                        attr_line = self._format_attribute_for_plantuml(attr_name, attr_info)
                                        f.write(f'{indent_str}    {attr_line}\n')
                                    f.write(f'{indent_str}    --\n')
                            if include_methods and cls in self.class_methods:
                                methods = self.class_methods[cls]
                                for method_info in methods:
                                    method_line = self._format_method_for_plantuml(method_info)
                                    if method_line:
                                        f.write(f'{indent_str}    {method_line}\n')
                            f.write(f'{indent_str}  }}\n')
                        f.write(f'{indent_str}}}\n\n')
                for key, subnode in node.items():
                    if key == '_files':
                        continue
                    escaped_package_name = f'"{key}"' if '.' in key else key
                    f.write(f'{indent_str}package {escaped_package_name} <<Folder>> {{\n')
                    write_tree(subnode, indent + 1)
                    f.write(f'{indent_str}}}\n\n')
            write_tree(tree)
            for child, parents in self.inheritance.items():
                child_id = sanitize(child)
                for parent in parents:
                    if parent in self.external_classes:
                        parent_id = sanitize(parent)
                        if parent_id not in declared_classes:
                            declare_class(parent, external=True)
                    else:
                        parent_id = sanitize(parent)
                    relationship = f"{parent_id} <|-- {child_id}"
                    if relationship not in declared_relationships:
                        declared_relationships.add(relationship)
                        f.write(f"{relationship}\n")
            for cls, members in self.composition.items():
                cls_id = sanitize(cls)
                for member in members:
                    if member in self.external_classes:
                        member_id = sanitize(member)
                        if member_id not in declared_classes:
                            declare_class(member, external=True)
                    else:
                        member_id = sanitize(member)
                    relationship = f"{cls_id} --> {member_id} : has-a"
                    if relationship not in declared_relationships:
                        declared_relationships.add(relationship)
                        f.write(f"{relationship}\n")
            f.write("\n@enduml\n")

    def print_analysis_summary(self):
        print("\n=== 분석 결과 요약 ===")
        print(f"발견된 패키지 수: {len(self.packages)}")
        print(f"발견된 클래스 수: {len(self.class_modules)}")
        print(f"외부 클래스 수: {len(self.external_classes)}")
        print(f"상속 관계 수: {sum(len(parents) for parents in self.inheritance.values())}")
        print(f"조합 관계 수: {sum(len(members) for members in self.composition.values())}")
        total_attributes = sum(len(attrs) for attrs in self.class_attributes.values())
        total_methods = sum(len(methods) for methods in self.class_methods.values())
        print(f"총 속성 수: {total_attributes}")
        print(f"총 메서드 수: {total_methods}")
        print("\n패키지 목록:")
        for pkg in sorted(self.packages):
            print(f"  - {pkg}")
        print("\n외부 클래스 목록:")
        for ext_cls in sorted(self.external_classes):
            print(f"  - {ext_cls}")
        print("\n클래스별 속성 정보:")
        for cls_name, attributes in self.class_attributes.items():
            if attributes:
                simple_name = cls_name.split('.')[-1]
                print(f"  {simple_name}:")
                for attr_name, attr_info in attributes.items():
                    print(f"    - {attr_name} ({attr_info['type']}, {attr_info['visibility']}, {attr_info['data_type']})") 