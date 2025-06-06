import os
from typing import Dict, List

from collections import defaultdict
from pyclassanalyzer.types import AnalysisResult

class PlantUMLGenerator:
    """PlantUML 다이어그램을 생성하는 클래스"""
    
    def __init__(self, result: AnalysisResult):
        self.result = result

    def generate_diagram(self, output_file: str = "class_diagram.puml", include_attributes: bool = True, include_methods: bool = True) -> None:
        """PlantUML 다이어그램 생성"""
        modules = defaultdict(list)
        for cls, mod in self.result.class_modules.items():
            modules[mod].append(cls)
        
        tree = self._build_module_tree(modules)
        
        with open(output_file, "w", encoding="utf-8") as f:
            self._write_header(f)
            self._write_classes(f, tree, modules, include_attributes, include_methods)
            self._write_relationships(f)
            f.write("\n@enduml\n")

    def _build_module_tree(self, modules: Dict[str, List[str]]) -> Dict:
        """모듈 트리 구성"""
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
        return tree

    def _write_header(self, f) -> None:
        """PlantUML 헤더 작성"""
        f.write("@startuml\n\n")
        f.write('skinparam class {\n')
        f.write('    BackgroundColor<<External>> LightBlue\n')
        f.write('}\n\n')

    def _write_classes(self, f, tree: Dict, modules: Dict[str, List[str]], include_attributes: bool, include_methods: bool) -> None:
        """클래스 정의 작성"""
        declared_classes = set()
        def declare_class(cls_full_name: str, external: bool = False) -> str:
            cls_id = cls_full_name  # full name 그대로 사용
            if cls_id not in declared_classes:
                declared_classes.add(cls_id)
                simple_name = cls_full_name.split(".")[-1]
                if external:
                    f.write(f'class {cls_id} as "{simple_name}" <<External>>\n')
                else:
                    f.write(f'class {cls_id} as "{simple_name}"\n')
            return cls_id
        def write_tree(node: Dict, indent: int = 0) -> None:
            indent_str = "  " * indent
            if '_files' in node:
                for mod in node['_files']:
                    if mod in self.result.module_to_file:
                        file_name = self.result.module_to_file[mod]
                        file_name_without_ext = os.path.splitext(file_name)[0]
                    else:
                        module_parts = mod.split('.')
                        file_name_without_ext = module_parts[-1]
                    escaped_file_name = f'"{file_name_without_ext}"' if '.' in file_name_without_ext else file_name_without_ext
                    f.write(f'{indent_str}frame {escaped_file_name} {{\n')
                    for cls in modules.get(mod, []):
                        cls_id = cls  # full name 그대로 사용
                        simple_name = cls.split(".")[-1]
                        f.write(f'{indent_str}  class {cls_id} as "{simple_name}" {{\n')
                        if include_attributes and cls in self.result.class_attributes:
                            attributes = self.result.class_attributes[cls]
                            if attributes:
                                for attr_name, attr_info in attributes.items():
                                    attr_line = self._format_attribute(attr_name, attr_info)
                                    f.write(f'{indent_str}    {attr_line}\n')
                                f.write(f'{indent_str}    --\n')
                        if include_methods and cls in self.result.class_methods:
                            methods = self.result.class_methods[cls]
                            for method_info in methods:
                                method_line = self._format_method(method_info)
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

    def _write_relationships(self, f) -> None:
        """클래스 간 관계 작성 (full name 기준, 외부는 실제로 없는 경우만 External)"""
        declared_classes = set()
        declared_relationships = set()
        def declare_class(cls_full_name: str, external: bool = False) -> str:
            cls_id = cls_full_name  # full name 그대로 사용
            if cls_id not in declared_classes:
                declared_classes.add(cls_id)
                simple_name = cls_full_name.split(".")[-1]
                if external:
                    f.write(f'class {cls_id} as "{simple_name}" <<External>>\n')
                else:
                    f.write(f'class {cls_id} as "{simple_name}"\n')
            return cls_id
        for child, parents in self.result.inheritance.items():
            child_id = child  # full name 그대로 사용
            for parent in parents:
                parent_id = parent  # full name 그대로 사용
                if self._is_external_class(parent):
                    if parent_id not in declared_classes:
                        declare_class(parent, external=True)
                else:
                    if parent_id not in declared_classes:
                        declare_class(parent, external=False)
                relationship = f"{parent_id} <|-- {child_id}"
                if relationship not in declared_relationships:
                    declared_relationships.add(relationship)
                    f.write(f"{relationship}\n")
        for cls, members in self.result.composition.items():
            cls_id = cls  # full name 그대로 사용
            for member in members:
                member_id = member  # full name 그대로 사용
                if self._is_external_class(member):
                    if member_id not in declared_classes:
                        declare_class(member, external=True)
                else:
                    if member_id not in declared_classes:
                        declare_class(member, external=False)
                relationship = f"{cls_id} --> {member_id} : has-a"
                if relationship not in declared_relationships:
                    declared_relationships.add(relationship)
                    f.write(f"{relationship}\n")

    def _is_external_class(self, class_name: str) -> bool:
        # class_name이 class_modules에 없으면 외부로 간주
        return class_name not in self.result.class_modules

    def _sanitize_name(self, name: str) -> str:
        """이름 정규화"""
        return "".join(c if c.isalnum() else "_" for c in name)

    def _format_attribute(self, attr_name: str, attr_info: Dict) -> str:
        """속성 포맷팅"""
        visibility_symbol = {
            'public': '+',
            'protected': '#',
            'private': '-'
        }
        
        symbol = visibility_symbol.get(attr_info['visibility'], '+')
        data_type = attr_info.get('data_type', 'object')
        
        # 타입 정보 간소화
        if data_type in ['int', 'str', 'float', 'bool', 'list', 'dict', 'set', 'tuple']:
            type_str = f": {data_type}"
        elif data_type == 'property':
            type_str = " {property}"
        else:
            type_str = f": {data_type}" if data_type != 'object' else ""
        
        return f"{symbol}{attr_name}{type_str}"

    def _format_method(self, method_info: Dict) -> str:
        """메서드 포맷팅"""
        visibility_symbol = {
            'public': '+',
            'protected': '#',
            'private': '-'
        }
        
        symbol = visibility_symbol.get(method_info['visibility'], '+')
        method_name = method_info['name']
        
        # 특수 메서드 처리
        if method_name in ['__init__', '__str__', '__repr__']:
            return f"{symbol}{method_name}()"
        
        # 프로퍼티는 속성으로 이미 표시되므로 제외
        if method_info.get('is_property', False):
            return None
        
        # 파라미터 간소화 (너무 길면 생략)
        params = method_info.get('params', [])
        if len(params) <= 2:
            param_str = ', '.join(params)
        else:
            param_str = f"{params[0]}, ..."
        
        param_part = f"({param_str})" if param_str else "()"
        
        # 데코레이터 정보 추가
        decorators = method_info.get('decorators', [])
        decorator_str = ""
        if decorators:
            if 'staticmethod' in decorators:
                decorator_str = " {static}"
            elif 'classmethod' in decorators:
                decorator_str = " {class}"
        
        return f"{symbol}{method_name}{param_part}{decorator_str}" 