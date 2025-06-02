from collections import defaultdict

class Registry:
    def __init__(self):
        self.enabled = True
    
    def disable(self):
        self.enabled = False

class ClassRegistry(Registry):
    def __init__(self):
        super().__init__()
        self.class_to_module = {} # 클래스명(전체) -> 모듈명 매핑
        self.simple_to_full = {} # 단순 클래스명 -> 전체 클래스명 매핑
        self.external_classes = set() # 외부 클래스 집합
        
        self.class_attributes = defaultdict(dict)   # 클래스별 속성 정보
        self.class_methods = defaultdict(list) 

    def add_class(self, full_class: str, module: str):
        self.class_to_module[full_class] = module
        self.simple_to_full[full_class.split('.')[-1]] = full_class

    def get_full_class(self, simple_name: str):
        return self.simple_to_full.get(simple_name)
    
    def add_external_class(self, class_name: str):
        self.external_classes.add(class_name)
    
    def add_class_attribute(self, class_name: str, attribute_name: str, attribute_type: str):
        self.class_attributes[class_name][attribute_name] = attribute_type
    
    def add_class_method(self, class_name: str, method_name: str, method_type: str):
        self.class_methods[class_name].append(method_name)

class RelationRegistry(Registry):
    def __init__(self):
        super().__init__()
        self.inheritance = defaultdict(list)  # child → list of base class names
        self.composition = defaultdict(set) # child → set of base class names

    def add_inheritance(self, child: str, bases: list):
        self.inheritance[child].extend(bases)

    def get_parents(self, class_name: str):
        return self.inheritance.get(class_name, [])
    
    def add_composition(self, child: str, bases: set):
        self.composition[child].update(bases)
    

class ImportRegistry(Registry):
    def __init__(self):
        super().__init__()
        self.imports = defaultdict(list)  # module → list of imported modules

    def add_import(self, from_mod: str, to_mod: str):
        self.imports[from_mod].append(to_mod)

    def get_imports(self, module: str):
        return self.imports.get(module, [])

class ModuleRegistry(Registry):
    def __init__(self):
        super().__init__()
        self.module_to_file = {}
        self.project_modules = set()

    def add_module(self, module: str, file_name: str):
        self.module_to_file[module] = file_name
        self.project_modules.add(module)

class PackageRegistry(Registry):
    def __init__(self):
        super().__init__()
        self.packages = set()

    def add_package(self, pkg: str):
        self.packages.add(pkg)