import ast

from pyclass_analyzer.types.result import CollectorResult

class Visitor(ast.NodeVisitor):
    def __init__(self, result: CollectorResult):
        self.current_module = None
        self.current_class = None

        

# class Visitor(ast.NodeVisitor):
#     def __init__(self, result):
#         self.result = result
#         self.current_module = None
#         self.current_class = None
    
#     def insert_current_module(self, module_path: str):
#         self.current_module = module_path

#     def visit_Import(self, node):
#         """import 문 처리"""
#         for alias in node.names:
#             module_name = alias.name
#             alias_name = alias.asname if alias.asname else alias.name
#             self.result.import_registry.add_import(self.current_module, alias_name)
            
#             # 외부 라이브러리 판정 (표준 라이브러리나 서드파티 라이브러리)
#             if not self._is_internal_module(module_name):
#                 # 해당 모듈의 모든 클래스를 외부로 간주
#                 pass  # 실제 클래스 사용 시점에서 판정

#     def visit_ImportFrom(self, node):
#         """from ... import ... 문 처리"""
#         if node.module:
#             for alias in node.names:
#                 imported_name = alias.name
#                 alias_name = alias.asname if alias.asname else alias.name
#                 full_name = f"{node.module}.{imported_name}"
#                 self.result.import_registry.add_import(self.current_module, full_name)
                
#                 # 외부 라이브러리에서 import한 클래스인지 판정
#                 if not self._is_internal_module(node.module):
#                     self.result.class_registry.external_classes.add(alias_name)

#     def _is_internal_module(self, module_name):
#         """모듈이 프로젝트 내부 모듈인지 판정"""
#         if not module_name:
#             return True
            
#         # 상대 import (., ..)로 시작하면 내부 모듈
#         if module_name.startswith('.'):
#             return True
            
#         # 프로젝트 내 모듈들과 비교
#         module_parts = module_name.split('.')
        
#         # 첫 번째 부분이 프로젝트 패키지 중 하나와 일치하면 내부
#         if module_parts[0] in self.result.package_registry.packages:
#             return True
            
#         # 알려진 프로젝트 모듈과 일치하면 내부
#         if module_name in self.result.module_registry.modules:
#             return True
            
#         # 표준 라이브러리나 외부 라이브러리로 간주
#         return False
    
#     def _get_base_name(self, base):
#         if isinstance(base, ast.Name):
#             return base.id
#         try:
#             return ast.unparse(base)
#         except Exception:
#             return str(base)

#     def visit_ClassDef(self, node):
#         class_name = f"{self.current_module}.{node.name}" if self.current_module else node.name
#         self.result.class_registry.class_module[class_name] = self.current_module if self.current_module else ""

#         # 단순 클래스명 매핑 추가 (동일한 단순명이 있으면 전체명으로 구분)
#         simple_name = node.name
#         if simple_name in self.result.class_registry.simple_to_full:
#             # 이미 존재하는 경우, 전체명으로 구분
#             existing_full = self.result.class_registry.simple_to_full[simple_name]
#             print(f"Warning: Duplicate class name '{simple_name}' found. "
#                   f"Existing: {existing_full}, New: {class_name}")
#         self.result.class_registry.simple_to_full[simple_name] = class_name

#         # 상속관계 분석
#         bases = [self._get_base_name(base) for base in node.bases]
#         for base in bases:
#             # import된 클래스인지 확인
#             if base in self.result.import_registry.imports.get(self.current_module, {}):
#                 imported_full_name = self.result.import_registry.imports[self.current_module][base]
#                 # 외부 라이브러리에서 import된 클래스인지 확인
#                 if not self._is_internal_import(imported_full_name):
#                     self.result.class_registry.external_classes.add(base)
#                     self.result.relation_registry.inheritance[class_name].append(base)
#                 else:
#                     # 내부 모듈의 클래스 - 전체 이름으로 매핑
#                     base_full = self.result.class_registry.class_module.get(base, base)
#                     self.result.relation_registry.inheritance[class_name].append(base_full)
#             else:
#                 # import되지 않은 클래스 - 프로젝트 내에서 찾기
#                 base_full = self.result.class_registry.class_module.get(base, base)
#                 if base_full in self.result.class_registry.class_module:
#                     # 프로젝트 내 클래스 발견
#                     self.result.relation_registry.inheritance[class_name].append(base_full)
#                 elif base in self.result.class_registry.class_module:
#                     # 단순명으로 매핑된 클래스 발견
#                     self.result.relation_registry.inheritance[class_name].append(self.result.class_registry.class_module[base])
#                 else:
#                     # 정의되지 않은 클래스는 외부로 간주
#                     self.result.class_registry.external_classes.add(base)
#                     self.result.relation_registry.inheritance[class_name].append(base)

#         self.current_class = class_name
        
#         # 클래스 내부 속성 및 메서드 분석
#         self._analyze_class_members(node, class_name)
        
#         self.generic_visit(node)
#         self.current_class = None

#     def _analyze_class_members(self, node, class_name):
#         """클래스 멤버(속성, 메서드) 분석"""
#         attributes = {}
#         methods = []
        
#         for item in node.body:
#             # 클래스 변수 (직접 할당)
#             if isinstance(item, ast.Assign):
#                 for target in item.targets:
#                     if isinstance(target, ast.Name):
#                         attr_name = target.id
#                         attr_type = self._get_attribute_type(item.value)
#                         visibility = self._get_visibility(attr_name)
                        
#                         attributes[attr_name] = {
#                             'type': 'class_variable',
#                             'data_type': attr_type,
#                             'visibility': visibility,
#                             'line': item.lineno
#                         }
            
#             # 메서드 및 프로퍼티 분석
#             elif isinstance(item, ast.FunctionDef):
#                 method_name = item.name
#                 visibility = self._get_visibility(method_name)
                
#                 # 데코레이터 확인
#                 decorators = []
#                 is_property = False
#                 for decorator in item.decorator_list:
#                     if isinstance(decorator, ast.Name):
#                         dec_name = decorator.id
#                         decorators.append(dec_name)
#                         if dec_name == 'property':
#                             is_property = True
#                     elif isinstance(decorator, ast.Attribute):
#                         if hasattr(decorator, 'attr'):
#                             decorators.append(decorator.attr)
                
#                 # 메서드 정보 저장
#                 method_info = {
#                     'name': method_name,
#                     'visibility': visibility,
#                     'decorators': decorators,
#                     'is_property': is_property,
#                     'line': item.lineno,
#                     'params': [arg.arg for arg in item.args.args[1:]]  # self 제외
#                 }
#                 methods.append(method_info)
                
#                 # 프로퍼티인 경우 속성으로도 저장
#                 if is_property:
#                     attributes[method_name] = {
#                         'type': 'property',
#                         'data_type': 'property',
#                         'visibility': visibility,
#                         'line': item.lineno
#                     }
                
#                 # __init__ 메서드에서 인스턴스 변수 찾기
#                 if method_name == '__init__':
#                     instance_attrs = self._analyze_init_method(item)
#                     attributes.update(instance_attrs)
                
#                 # 다른 메서드에서 동적 속성 찾기
#                 else:
#                     dynamic_attrs = self._analyze_method_for_attributes(item)
#                     for attr_name, attr_info in dynamic_attrs.items():
#                         if attr_name not in attributes:  # 중복 방지
#                             attributes[attr_name] = attr_info
        
#         self.result.class_registry.class_attributes[class_name] = attributes
#         self.result.class_registry.class_methods[class_name] = methods

#     def _analyze_init_method(self, init_node):
#         """__init__ 메서드에서 인스턴스 변수 분석"""
#         attributes = {}
        
#         for stmt in ast.walk(init_node):
#             if isinstance(stmt, ast.Assign):
#                 for target in stmt.targets:
#                     if isinstance(target, ast.Attribute):
#                         if isinstance(target.value, ast.Name) and target.value.id == 'self':
#                             attr_name = target.attr
#                             attr_type = self._get_attribute_type(stmt.value)
#                             visibility = self._get_visibility(attr_name)
                            
#                             attributes[attr_name] = {
#                                 'type': 'instance_variable',
#                                 'data_type': attr_type,
#                                 'visibility': visibility,
#                                 'line': stmt.lineno
#                             }
        
#         return attributes

#     def _analyze_method_for_attributes(self, method_node):
#         """메서드에서 동적으로 추가되는 속성 분석"""
#         attributes = {}
        
#         for stmt in ast.walk(method_node):
#             if isinstance(stmt, ast.Assign):
#                 for target in stmt.targets:
#                     if isinstance(target, ast.Attribute):
#                         if isinstance(target.value, ast.Name) and target.value.id == 'self':
#                             attr_name = target.attr
#                             attr_type = self._get_attribute_type(stmt.value)
#                             visibility = self._get_visibility(attr_name)
                            
#                             attributes[attr_name] = {
#                                 'type': 'dynamic_attribute',
#                                 'data_type': attr_type,
#                                 'visibility': visibility,
#                                 'line': stmt.lineno,
#                                 'method': method_node.name
#                             }
        
#         return attributes

#     def _get_attribute_type(self, value_node):
#         """값 노드에서 데이터 타입 추정"""
#         if isinstance(value_node, ast.Constant):
#             return type(value_node.value).__name__
#         elif isinstance(value_node, ast.Str):  # Python < 3.8
#             return 'str'
#         elif isinstance(value_node, ast.Num):  # Python < 3.8
#             return 'int' if isinstance(value_node.n, int) else 'float'
#         elif isinstance(value_node, ast.List):
#             return 'list'
#         elif isinstance(value_node, ast.Dict):
#             return 'dict'
#         elif isinstance(value_node, ast.Set):
#             return 'set'
#         elif isinstance(value_node, ast.Tuple):
#             return 'tuple'
#         elif isinstance(value_node, ast.Call):
#             if isinstance(value_node.func, ast.Name):
#                 return value_node.func.id
#             else:
#                 return 'object'
#         else:
#             return 'object'

#     def _get_visibility(self, name):
#         """속성/메서드명에서 가시성 판단"""
#         if name.startswith('__') and not name.endswith('__'):
#             return 'private'
#         elif name.startswith('_'):
#             return 'protected'
#         else:
#             return 'public'

#     def _is_internal_import(self, imported_name):
#         """import된 이름이 내부 모듈에서 온 것인지 판정"""
#         if '.' in imported_name:
#             module_part = imported_name.rsplit('.', 1)[0]
#             return self._is_internal_module(module_part)
#         return self._is_internal_module(imported_name)

#     def visit_Assign(self, node):
#         # self.xxx = SomeClass(...)
#         if isinstance(node.targets[0], ast.Attribute):
#             attr = node.targets[0]
#             if isinstance(attr.value, ast.Name) and attr.value.id == 'self':
#                 if isinstance(node.value, ast.Call):
#                     if isinstance(node.value.func, ast.Name):
#                         member_class_short = node.value.func.id
#                         if self.current_class:
#                             # import된 클래스인지 확인
#                             if member_class_short in self.result.import_registry.imports.get(self.current_module, {}):
#                                 imported_full_name = self.result.import_registry.imports[self.current_module][member_class_short]
#                                 if not self._is_internal_import(imported_full_name):
#                                     self.result.class_registry.external_classes.add(member_class_short)
#                                 else:
#                                     # 내부 클래스
#                                     member_class = self.result.class_registry.class_module.get(member_class_short, member_class_short)
#                                     self.result.relation_registry.composition[self.current_class].add(member_class)
#                             elif member_class_short in self.result.class_registry.class_module:
#                                 # 프로젝트 내 클래스
#                                 member_class = self.result.class_registry.class_module[member_class_short]
#                                 self.result.relation_registry.composition[self.current_class].add(member_class)
#                             else:
#                                 # 정의되지 않은 클래스는 외부로 처리
#                                 self.result.class_registry.external_classes.add(member_class_short)
#         self.generic_visit(node)
