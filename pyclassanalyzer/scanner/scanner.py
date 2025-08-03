import ast
import os
from datetime import datetime
from typing import Optional, List

from pyclassanalyzer.analyzer.package import PackageAnalyzer, analyze_module
from pyclassanalyzer.visitors.visitor import Visitor
from pyclassanalyzer.network.classgraph import ClassGraph
from pyclassanalyzer.generators.plantuml import PlantUMLGenerator
from pyclassanalyzer.config import TomlConfig


class GraphScanner:
    def __init__(self, path: str, config: TomlConfig):
        self.path = path
        self.config = config
        self.graph = ClassGraph()
        self.visitor = Visitor(graph=self.graph, config=config)
        self.plantuml_generator = PlantUMLGenerator(config=config)
    
    def analyze(self):
        """Analyze the class diagram from the package tree."""
        
        excludes = self.config.get('exclude')['directories']
        
        package_analyzer = PackageAnalyzer(path=self.path)
        package_tree = package_analyzer.analyze()
        
        # NOTE: To avoid read file twice, 
        # collect all nodes first, then visit them again .
        all_nodes = []
        for _, tree in package_tree.traverse(base_path=self.path, excludes=excludes):
            for node in tree.body:
                all_nodes.append(node)
                self.visitor.visit(node) 
        
        for node in all_nodes:
            self.visitor.visit(node) 
    
    def print_plantuml(self, output_path: Optional[str] = None, title: Optional[str] = None):
        """Print the class diagram to the console.
        
        Args:
            output_path (Optional[str]): The path to save the class diagram.
            title (Optional[str]): The title of the class diagram.
        """
        
        # title
        if title is None:
            project_name = os.path.basename(os.path.abspath(self.path))
            title = f"{project_name} Class Diagram"
        
        # print to console
        plantuml_content = self.plantuml_generator.generate_plantuml(self.graph, title)
        print("=" * 60)
        print(f"PlantUML Class Diagram for: {self.path}")
        print("=" * 60)
        print(plantuml_content)
        print("=" * 60)
        
        # save to file
        if output_path:
            success = self.plantuml_generator.save_to_file(self.graph, output_path, title)
            if success:
                print(f"PlantUML file saved: {output_path}")
            else:
                print("Failed to save file.")
        
        return plantuml_content
    
    def save_plantuml(self, output_path: str, title: Optional[str] = None) -> bool:
        """Save the class diagram to a file.
        
        Args:
            output_path (str): The path to save the class diagram.
            title (Optional[str]): The title of the class diagram.
            
        Returns:
            bool: True if the class diagram is saved successfully, False otherwise.
        
        NOTE:
            If the output_path is not specified, the class diagram is saved to the current directory.
        """
        
        if title is None:
            project_name = os.path.basename(os.path.abspath(self.path))
            title = f"{project_name} Class Diagram"
        
        return self.plantuml_generator.save_to_file(self.graph, output_path, title)
    
    def get_plantuml_content(self, title: Optional[str] = None) -> str:
        """Get the class diagram as a string.
        
        Args:
            title (Optional[str]): The title of the class diagram.
            
        Returns:
            str: The class diagram as a string.
        """
        
        if title is None:
            project_name = os.path.basename(os.path.abspath(self.path))
            title = f"{project_name} Class Diagram"
        
        return self.plantuml_generator.generate_plantuml(self.graph, title)
    
    def print_graph_count(self):
        """Print the number of nodes and relations in the class graph."""
        
        node_cnt = len(self.graph.nodes)
        relation_cnt = len(self.graph.relations)
        
        if node_cnt == 0:
            print("Warning: No classes found. Please check the path.")
        else:
            print(f"Total {node_cnt} classes and {relation_cnt} relations found.")
    
    def print_analysis_summary(self):
        """Print the analysis summary."""
        
        print(f"Analysis completed!")
        print(f"- Found {len(self.graph.nodes)} classes")
        print(f"- Found {len(self.graph.relations)} relations")
        
        if self.graph.nodes:
            print("- Class list:")
            for node_name in sorted(self.graph.nodes.keys()):
                print(f"  * {node_name}")
        
        if self.graph.relations:
            print("- Relation list:")
            relation_counts = {}
            for rel in self.graph.relations:
                rel_type = rel.type_.value if hasattr(rel.type_, 'value') else str(rel.type_)
                relation_counts[rel_type] = relation_counts.get(rel_type, 0) + 1
            
            for rel_type, count in relation_counts.items():
                print(f"  * {rel_type}: {count}개")
        
        print("-" * 40)
    
    def generate_auto_filename(self) -> str:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        project_name = os.path.basename(os.path.abspath(self.path))
        return f"{project_name}_{timestamp}.puml"
        