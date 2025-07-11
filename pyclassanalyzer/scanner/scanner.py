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
        self._config = config
        self.graph = ClassGraph()
        self.visitor = Visitor(graph=self.graph, config=config)
        self.plantuml_generator = PlantUMLGenerator(config=config)
        
        
        
    def analyze(self):
        """
        패키지 분석 및 AST 순회
        정확성을 위해 2회 방문
        """
        excludes = self._config.get('exclude')['directories']
        
        package_analyzer = PackageAnalyzer(path=self.path)
        package_tree = package_analyzer.analyze()
        
        # try 1
        for _, tree in package_tree.traverse(
            base_path=self.path, excludes=excludes
        ):
            for node in tree.body:  # 최상위 노드만 탐색
                self.visitor.visit(node)
        
        # try 2 
        for _, tree in package_tree.traverse(
            base_path=self.path, excludes=excludes
        ):
            for node in tree.body:  # 최상위 노드만 탐색
                self.visitor.visit(node)
    
    def print_plantuml(self, output_path: Optional[str] = None, title: Optional[str] = None):
        """AST 분석 결과를 PlantUML 다이어그램으로 출력"""
        
        # 기본 제목 설정
        if title is None:
            project_name = os.path.basename(os.path.abspath(self.path))
            title = f"{project_name} Class Diagram"
        
        # 콘솔에 출력
        plantuml_content = self.plantuml_generator.generate_plantuml(self.graph, title)
        print("=" * 60)
        print(f"PlantUML Class Diagram for: {self.path}")
        print("=" * 60)
        print(plantuml_content)
        print("=" * 60)
        
        # 파일로 저장 (output_path가 지정된 경우)
        if output_path:
            success = self.plantuml_generator.save_to_file(self.graph, output_path, title)
            if success:
                print(f"PlantUML 파일이 저장되었습니다: {output_path}")
            else:
                print("파일 저장에 실패했습니다.")
        
        return plantuml_content
    
    def save_plantuml(self, output_path: str, title: Optional[str] = None) -> bool:
        
        if title is None:
            project_name = os.path.basename(os.path.abspath(self.path))
            title = f"{project_name} Class Diagram"
        
        return self.plantuml_generator.save_to_file(self.graph, output_path, title)
    
    def get_plantuml_content(self, title: Optional[str] = None) -> str:
        
        if title is None:
            project_name = os.path.basename(os.path.abspath(self.path))
            title = f"{project_name} Class Diagram"
        
        return self.plantuml_generator.generate_plantuml(self.graph, title)
    
    def print_graph_count(self):
        node_cnt = len(self.graph.nodes)
        relation_cnt = len(self.graph.relations)
        
        if node_cnt == 0:
            print("Warning: 분석된 클래스가 없습니다. 경로를 확인해주세요.")
        else:
            print(f"총 {node_cnt}개의 클래스와 {relation_cnt}개의 관계를 발견했습니다.")
    
    def print_analysis_summary(self):
        print(f"분석 완료!")
        print(f"- 발견된 클래스: {len(self.graph.nodes)}개")
        print(f"- 발견된 관계: {len(self.graph.relations)}개")
        
        if self.graph.nodes:
            print("- 클래스 목록:")
            for node_name in sorted(self.graph.nodes.keys()):
                print(f"  * {node_name}")
        
        if self.graph.relations:
            print("- 관계 목록:")
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
        