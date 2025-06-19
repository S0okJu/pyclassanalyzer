import ast 

from pyclassanalyzer.analyzer.package import PackageAnalyzer

class AnalyzerManager:
    def __init__(self, path:str):
        self.path = path 
    
    def analyze(self):
        package_analyzer = PackageAnalyzer(path=self.path)
        package_tree = package_analyzer.analyze()
        
        for full_path, tree in package_tree.traverse(base_path=self.path):
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    pass     
        
        
        
        