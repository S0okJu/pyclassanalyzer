import ast 

from pyclassanalyzer.analyzer.package import PackageAnalyzer
from pyclassanalyzer.visitors.visitor import Visitor
from pyclassanalyzer.network.classgraph import ClassGraph

class GraphScanner:
    def __init__(self, path:str):
        self.path = path
        self.graph = ClassGraph()
        self.visitor = Visitor(graph=self.graph)
    
    def analyze(self):
        package_analyzer = PackageAnalyzer(path=self.path)
        package_tree = package_analyzer.analyze()
        
        for full_path, tree in package_tree.traverse(base_path=self.path):
            self.visitor.visit(tree)
            
        
        
        