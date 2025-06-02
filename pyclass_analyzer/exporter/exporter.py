import os
from collections import defaultdict

from pyclass_analyzer.types.result import Result
from pyclass_analyzer.config.config import Config

class PlantUMLExporter:
    def __init__(self, config:Config, result: Result):
        self.result = result
        self.config = config
        self.declared_classes = set()
        self.declared_relationships = set()
        self.modules = defaultdict(list)
        
    def _sanitize(self, name) -> str:
        return "".join(c if c.isalnum() else "_" for c in name)
    
    def _init_module(self) :
        self.modules.clear()  # clear 해서 중복 누적 방지
        for cls_, mod in self.result.class_registry.class_to_module.items():
            self.modules[mod].append(cls_)

    
    def _init_tree(self) -> dict:
        # 패키지 트리 생성 - 단순화된 접근
        tree = {}
        
        # 먼저 모든 모듈을 순회하면서 트리 구조 생성
        for mod, classes in self.modules.items():
            if not mod:
                continue
                
            parts = mod.split('.')
            current_node = tree
            
            # 패키지 부분들을 처리 (마지막 파일명 제외)
            for i in range(len(parts) - 1):
                package_name = parts[i]
                if package_name not in current_node:
                    current_node[package_name] = {}
                current_node = current_node[package_name]
            
            # 마지막 부분(파일)을 _files에 추가
            if '_files' not in current_node:
                current_node['_files'] = []
            current_node['_files'].append(mod)
            
        return tree
    
    def _declare_class(self, f, cls_name, external=False):
        cls_id = self._sanitize(cls_name)
        if cls_id not in self.declared_classes:
            self.declared_classes.add(cls_id)
            simple_name = cls_name.split(".")[-1]
            if external:
                f.write(f'class {cls_id} as "{simple_name}" <<External>>\n')
            else:
                f.write(f'class {cls_id} as "{simple_name}"\n')
        return cls_id

    def _write_tree(self, f, node, indent=0):
        indent_str = "  " * indent
        
        # 파일들 처리
        if '_files' in node:
            for mod in node['_files']:
                if mod in self.result.module_registry.module_to_file:
                    file_name = self.result.module_registry.module_to_file[mod]
                    # .py 확장자 제거
                    file_name_without_ext = os.path.splitext(file_name)[0]
                else:
                    module_parts = mod.split('.')
                    file_name_without_ext = module_parts[-1]
                
                escaped_file_name = f'"{file_name_without_ext}"' if '.' in file_name_without_ext else file_name_without_ext
                f.write(f'{indent_str}frame {escaped_file_name} {{\n')
                
                # 해당 모듈의 클래스들 선언 (속성과 메서드 포함)
                for cls in self.modules.get(mod, []):
                    cls_id = self._sanitize(cls)
                    simple_name = cls.split(".")[-1]
                    
                    # 클래스 선언 시작
                    f.write(f'{indent_str}  class {cls_id} as "{simple_name}" {{\n')
                    
                    # 속성 추가
                    if self.config.include_attributes and cls in self.result.class_registry.class_attributes:
                        attributes = self.result.class_registry.class_attributes[cls]
                        if attributes:
                            for attr_name, attr_info in attributes.items():
                                attr_line = self._format_attribute_for_plantuml(attr_name, attr_info)
                                f.write(f'{indent_str}    {attr_line}\n')
                            f.write(f'{indent_str}    --\n')  # 속성과 메서드 구분선
                    
                    # 메서드 추가
                    if self.config.include_methods and cls in self.result.class_registry.class_methods:
                        methods = self.result.class_registry.class_methods[cls]
                        for method_info in methods:
                            method_line = self._format_method_for_plantuml(method_info)
                            if method_line:  # None이 아닌 경우만 추가
                                f.write(f'{indent_str}    {method_line}\n')
                    
                    f.write(f'{indent_str}  }}\n')
                
                f.write(f'{indent_str}}}\n\n')
        
        # 하위 패키지들 처리
        for key, subnode in node.items():
            if key == '_files':
                continue
            escaped_package_name = f'"{key}"' if '.' in key else key
            f.write(f'{indent_str}package {escaped_package_name} <<Folder>> {{\n')
            self._write_tree(f, subnode, indent + 1)
            f.write(f'{indent_str}}}\n\n')


    def _write_inheritance(self, f):
        for child, parents in self.result.relation_registry.inheritance.items():
            child_id = self._sanitize(child)
            for parent in parents:
                if parent in self.result.class_registry.external_classes:
                    parent_id = self._sanitize(parent)
                    if parent_id not in self.declared_classes:
                        self._declare_class(f, parent, external=True)
                else:
                    parent_id = self._sanitize(parent)

                relationship = f"{parent_id} <|-- {child_id}"
                if relationship not in self.declared_relationships:
                    self.declared_relationships.add(relationship)
                    f.write(f"{relationship}\n")
        # for child, parents in self.result.relation_registry.inheritance.items():
        #     child_id = self._sanitize(child)
        #     for parent in parents:
        #         # 부모 클래스가 외부 클래스인지 확인
        #         if parent in self.result.class_registry.external_classes:
        #             parent_id = self._sanitize(parent)
        #             # 외부 클래스는 별도로 선언
        #             if parent_id not in self.declared_classes:
        #                 self._declare_class(f, parent, external=True)
        #         else:
        #             # 내부 클래스는 이미 프레임 안에 선언되어 있음
        #             parent_id = self._sanitize(parent)
                
        #         relationship = f"{parent_id} <|-- {child_id}"
        #         if relationship not in self.declared_relationships:
        #             self.declared_relationships.add(relationship)
        #             f.write(f"{relationship}\n")
    
    def _write_composition(self, f):
        # 포함 관계 그리기 (중복 방지)
        for cls, members in self.result.relation_registry.composition.items():
            cls_id = self._sanitize(cls)
            for member in members:
                if member in self.result.class_registry.external_classes:
                    member_id = self._sanitize(member)
                    if member_id not in self.declared_classes:
                        self._declare_class(f, member, external=True)
                else:
                    member_id = self._sanitize(member)
                
                relationship = f"{cls_id} --> {member_id} : has-a"
                if relationship not in self.declared_relationships:
                    self.declared_relationships.add(relationship)
                    f.write(f"{relationship}\n")
    # def _write_composition(self, f):
    #     # 포함 관계 그리기 (중복 방지)
    #     for cls, members in self.result.relation_registry.composition.items():
    #         cls_id = self._sanitize(cls)
    #         for member in members:
    #             # 멤버 클래스가 외부 클래스인지 확인
    #             if member in self.result.class_registry.external_classes:
    #                 member_id = self._sanitize(member)
    #                 # 외부 클래스는 별도로 선언
    #                 if member_id not in self.declared_classes:
    #                     self._declare_class(f, member, external=True)
    #             else:
    #                 # 내부 클래스는 이미 프레임 안에 선언되어 있음
    #                 member_id = self._sanitize(member)
                
    #             relationship = f"{cls_id} --> {member_id} : has-a"
    #             if relationship not in self.declared_relationships:
    #                 self.declared_relationships.add(relationship)
    #                 f.write(f"{relationship}\n")
    
    def export(self, filepath):
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("@startuml\n\n")

            f.write('skinparam class {\n')
            f.write('  BackgroundColor<<External>> LightBlue\n')
            f.write('}\n\n')

            self._init_module()
            tree = self._init_tree()
            self._write_tree(f,tree)
            self._write_inheritance(f)
            self._write_composition(f)

            f.write("@enduml\n")
        
