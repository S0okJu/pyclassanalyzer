from pyclass_analyzer.registry.registry import ClassRegistry, RelationRegistry, ImportRegistry, ModuleRegistry, PackageRegistry

class Result:
    def __init__(self):
        self.class_registry = ClassRegistry()
        self.relation_registry = RelationRegistry()
        self.import_registry = ImportRegistry()
        self.module_registry = ModuleRegistry()
        self.package_registry = PackageRegistry()
        self.current_module = None
