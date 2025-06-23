import ast
import os 

from typing import List
from pyclassanalyzer.network.package import PackageTree
from pyclassanalyzer.utils.path import find_root_name
def analyze_module(path: str) -> ast.Module:
    """
    
    """
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    tree = ast.parse(content)
    return tree 

class PackageAnalyzer:
    def __init__(self, path: str) -> None:
        self.path = path 
        
    def _discovery(self) -> List[str]:
        """
        Walk through all subdirectories under self.path
        
        Only include files inside directories that contain an `__init__.py` file,
        which indicates a Python Package
        """
        paths = []
        for root, _, files in os.walk(self.path):
                        
            for file in files:
                # 상대 경로로 변환 
                path = os.path.abspath(os.path.join(root, file)) 
                
                if '__init__.py' in files:
                    paths.append(path)
                    
        return paths
    
    def analyze(self) -> PackageTree:
        # init package tree 
        paths = self._discovery()
        root = find_root_name(self.path)
        
        package_tree = PackageTree(root = root)
        package_tree.build(paths=paths, base_path=self.path)
        
        return package_tree
        
        
        
        
        
        
        
            
        
            
        
         
    
        
        