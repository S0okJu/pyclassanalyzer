from collections import defaultdict

from config import Config
from result import Result

class Generator:
    def __init__(self, path, config):
        self.path = path
        self.config = config

class PlantumlGenerator(Generator):
    def __init__(self, path, config: Config, result: Result):
        super().__init__(path, config)
        self.result = result

    def _sanitize(self, name):
        return "".join(c if c.isalnum() else "_" for c in name)
    
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
    
    def _make_tree(self):
        modules = defaultdict(list)
        for cls, mod in self.result.class_modules.items():
            modules[mod].append(cls)

        # 패키지 트리 생성 - 단순화된 접근
        tree = {}
        
        # 먼저 모든 모듈을 순회하면서 트리 구조 생성
        for mod, classes in modules.items():
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
    
    
    
    def import_file(self, file_path):
        _make_tree()
        
        
