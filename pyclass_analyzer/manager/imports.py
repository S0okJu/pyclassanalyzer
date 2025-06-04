from typing import List, Set, defaultdict

class ImportsRecordManager:
    def __init__(self):
        self.imports = defaultdict(dict)
        self.packages = set()
        self.project_modules = set()
        self.external_classes = set()

    """
    Import(names=[alias(name='x', asname=None), alias(name='y', asname='z')])

    """
    def _add(self, module: str, alias):
        """
        ex) {
            "foo": {
                "y": "x"
            }
        }
        """
        module_name = alias.name
        alias_name = alias.asname if alias.asname else alias.name
        self.imports[module][alias_name] = module_name

    def is_exist(self, base, module):
        if self.imports.get(module,{}):
            return base in self.imports[module]
        return False
    
    def is_internal_module(self, module_name):
        """모듈이 프로젝트 내부 모듈인지 판정"""
        if not module_name:
            return True
            
        # 상대 import (., ..)로 시작하면 내부 모듈
        if module_name.startswith('.'):
            return True
            
        # 프로젝트 내 모듈들과 비교
        module_parts = module_name.split('.')
        
        # 첫 번째 부분이 프로젝트 패키지 중 하나와 일치하면 내부
        if module_parts[0] in self.packages:
            return True
            
        # 알려진 프로젝트 모듈과 일치하면 내부
        if module_name in self.project_modules:
            return True
            
        # 표준 라이브러리나 외부 라이브러리로 간주
        return False
    
    def add_external_class(self, class_name):
        self.external_classes.add(class_name)
    
    
    
    def visit_import(self,node):
        for alias in node.names:
            self._add(node.module, alias)

            # it is external module, so we don't need to analyze it
            if not self.is_internal_module(node.module):
                pass 
    
    def visit_import_from(self, node, module):
         if node.module:
            for alias in node.names:
                self._add(module, alias)
                
                if not self.is_internal_module(node.module):
                    self.external_classes.add(alias.asname if alias.asname else alias.name)
            
    