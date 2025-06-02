import ast
from pyclass_analyzer.visitor.visitor import ClassStructureVisitor, ImportVisitor

class ProjectParser:
    def __init__(self, files, result):
        self.files = files
        self.result = result

    def parse(self):
        for full_path, module_path, file in self.files:
            with open(full_path, 'r', encoding='utf-8') as f:
                try:
                    source = f.read()
                    tree = ast.parse(source, filename=file)
                    self.result.current_module = module_path

                    # 클래스 구조 분석
                    visitor = ClassStructureVisitor(self.result)
                    visitor.visit(tree)
                    
                    attribute_visitor = AttributeVisitor(self.result)
                    attribute_visitor.visit(tree)

                    # import 분석
                    import_visitor = ImportVisitor(self.result)
                    import_visitor.visit(tree)

                except Exception as e:
                    print(f"[ParseError] {file}: {e}")
