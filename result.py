from collections import defaultdict

class Result:
    def __init__(self):
        self.inheritance = defaultdict(list)       # 클래스 상속 관계
        self.composition = defaultdict(set)        # 클래스 조합 관계 (has-a)
        self.class_modules = {}                     # 클래스명(전체) -> 모듈명
        self.class_name_to_full = {}                # 단순 클래스명 -> 전체 클래스명 매핑
        self.current_class = None
        self.current_module = None
        self.packages = set()                       # 패키지명 집합
        self.external_classes = set()               # 외부 클래스 집합
        self.module_to_file = {}                    # 모듈명 -> 파일명+확장자 매핑
        self.imports = defaultdict(dict)            # 모듈별 import 정보
        self.project_modules = set()   
    
    def add_inheritance(self, child, parent):
        self.inheritance[child].append(parent)
        
    def add_composition(self, parent, child):
        self.composition[parent].add(child)
    
    def add_package(self, package):
        self.packages.add(package)
        
    def add_method(self, method_name):
        self.methods.add(method_name)
        
    def add_attribute(self, attribute_name):
        self.attributes.add(attribute_name)
        
    def add_class_attribute(self, class_name, attribute_name, attribute_type):
        self.class_attributes[class_name][attribute_name] = attribute_type
        
    def add_class_method(self, class_name, method_name, method_type):
        self.class_methods[class_name][method_name] = method_type
        
