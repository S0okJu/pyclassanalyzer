from typing import List, defaultdict
import ast
from pyclass_analyzer.manager import ImportsRecordManager, ClassRecordManager

class Scanner(ast.NodeVisitor):
    def __init__(self):
        self.record_manager = ClassRecordManager()
        self.import_manager = ImportsRecordManager()
        
        self.inheritance = defaultdict(list)

    def _get_base_name(self, base):
        if isinstance(base, ast.Name):
            return base.id
        try:
            return ast.unparse(base)
        except Exception:
            return str(base)
        
    def visit_ClassDef(self, node, current_module):
        
        record = ClassRecord(node.name, current_module)
        self.record_manager.add(record)
        
        # Analysis Inheritance 
        bases = [self._get_base_name(base) for base in node.bases]
        for base in bases:
            if self.import_manager.is_exist(base, current_module):
                if not self.import_manager.is_internal_module(base):
                    self.import_manager.add_external_class(base)
                    self.inheritance[record.full_name].append(base)
                else:
                    self.inheritance[record.full_name].append(self.import_manager.get(base, current_module))
            else:
                candidates = self.record_manager.get_by_name(base)
                if candidates:
                    for c in candidates:
                        self.inheritance[record.full_name].append(c.full_name)
                else:
                    self.import_manager.add_external_class(base)
                    self.inheritance[record.full_name].append(base)
                    
        self.generic_visit(node)
        

        