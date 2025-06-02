import ast


class Visitor(ast.NodeVisitor):
    def __init__(self, result):
        self.result = result


class ClassStructureVisitor(Visitor):
    def __init__(self, result):
        super().__init__(result)

    def visit_ClassDef(self, node):
        module = self.result.current_module
        full_class = f"{module}.{node.name}"
        base_classes = [self._get_base_name(b) for b in node.bases]

        self.result.class_registry.add_class(full_class, module)
        self.result.relation_registry.add_inheritance(full_class, base_classes)

    def _get_base_name(self, base):
        if isinstance(base, ast.Name):
            return base.id
        elif isinstance(base, ast.Attribute):
            return f"{self._get_base_name(base.value)}.{base.attr}"
        elif isinstance(base, ast.Subscript):
            return self._get_base_name(base.value)
        return 'UnknownBase'

class AttributeVisitor(Visitor):
    def __init__(self, result):
        super().__init__(result)

    def visit_Assign(self, node):
        pass

class ImportVisitor(Visitor):
    def __init__(self, result):
        super().__init__(result)

    def visit_Import(self, node):
        for alias in node.names:
            self.result.import_registry.add_import(self.result.current_module, alias.name)

    def visit_ImportFrom(self, node):
        mod = node.module or ""
        for alias in node.names:
            self.result.import_registry.add_import(self.result.current_module, f"{mod}.{alias.name}")
