import os
from typing import List

from pyclassanalyzer.network.classgraph import RelationType, ClassNode, ClassType
from pyclassanalyzer.utils.class_type import is_private, is_protected, is_magic

INDENT = "  "

def get_symbol(name:str) -> str:
    symbol = '+'
    if is_private(name):
        symbol = '-'
    elif is_protected(name):
        symbol = '#'
    
    return f"{symbol}{name}"

    
def streamline_fields(fields) -> str :
    if not fields:
        return ""
    
    if len(fields) <= 2:
        return ", ".join(fields)
    else:
        return f"{fields[0]}, ..."

class PlantUMLGenerator:    
    def __init__(self, config):
        """
        COMPOSITION = self.xxx
        USE = 함수 내에서 사용하는 경우 
        """
        self.relation_symbols = {
            RelationType.INHERITANCE: "--|>",
            RelationType.COMPOSITION: "*--",
            RelationType.DEPENDENCY: "..>",
        }
        self._config = config
    
    def _generate_class(self, node:ClassNode) -> str:
        line = []
        
        if node.type_ == ClassType.ENUM:
            line.append(f"enum {node.name} {{")
        elif node.type_ == ClassType.ABSTRACT:
            line.append(f"abstract class {node.name} {{")
        elif node.type_ == ClassType.DATACLASS:
            line.append(f"class {node.name} << (D,#FFDD55) >> {{")
            # >=2025.4 support
            # line.append(f"dataclass {node.name} {{")
        elif node.type_ == ClassType.EXCEPTION:
            line.append(f"exception {node.name} {{")
        else:
            line.append(f"class {node.name} {{")
        
        if hasattr(node, 'attributes') and node.attributes:
            for attr in node.attributes:
                line.append(f"  {get_symbol(attr)}")
        
        if hasattr(node, 'functions') and node.functions:
            for func in node.functions:
                # If "magic" is included in the [exclude] methods in the TOML config,
                # skip processing the Visit function 
                       
                # NOTE: The `__init__()` method is key to analyzing the relationship types between classes.
                # We filter out magic methods after gathering all function lists.
                exclude_magic = True if 'magic' in self._config.get('exclude')['methods'] else False
                if exclude_magic and is_magic(func.name):
                    continue
                  
                params = streamline_fields(getattr(func, 'fields', []))
                line.append(f"  {get_symbol(func.name)}({params})")
        
        line.append("}")
        return "\n".join(line)
    
    def _generate_relation(self, relation) -> str:
        """관계를 PlantUML 관계 정의로 변환"""
        # relation.type_가 Enum인지 확인
        if hasattr(relation.type_, 'value'):
            relation_type = relation.type_
        else:
            relation_type = relation.type_
            
        symbol = self.relation_symbols.get(relation_type, "--")
        
        # 관계에 라벨이 있는 경우
        label = ""
        if hasattr(relation, 'label') and relation.label:
            label = f" : {relation.label}"
        
        # 다중성 정보가 있는 경우
        multiplicity = ""
        if hasattr(relation, 'source_multiplicity') or hasattr(relation, 'target_multiplicity'):
            source_mult = getattr(relation, 'source_multiplicity', '')
            target_mult = getattr(relation, 'target_multiplicity', '')
            if source_mult or target_mult:
                multiplicity = f' "{source_mult}" {symbol} "{target_mult}"'
                symbol = ""
        
        return f"{relation.source} {symbol}{multiplicity} {relation.target}{label}"
    
    def debug_class_graph(self, class_graph):
        print("=== ClassGraph 디버깅 정보 ===")
        
        # 노드 정보 출력
        print(f"총 노드 수: {len(class_graph.nodes) if hasattr(class_graph, 'nodes') else 'nodes 속성 없음'}")
        if hasattr(class_graph, 'nodes'):
            for name, node in class_graph.nodes.items():
                print(f"노드: {name}")
                print(f"  - 타입: {type(node)}")
                print(f"  - 속성들: {[attr for attr in dir(node) if not attr.startswith('_')]}")
                if hasattr(node, 'attributes'):
                    print(f"  - attributes: {node.attributes}")
                if hasattr(node, 'functions'):
                    print(f"  - functions: {[f.name for f in node.functions] if node.functions else []}")
        
        # 관계 정보 출력
        print(f"\n총 관계 수: {len(class_graph.relations) if hasattr(class_graph, 'relations') else 'relations 속성 없음'}")
        if hasattr(class_graph, 'relations'):
            for i, relation in enumerate(class_graph.relations):
                print(f"관계 {i+1}:")
                print(f"  - 소스: {relation.source if hasattr(relation, 'source') else 'source 없음'}")
                print(f"  - 타겟: {relation.target if hasattr(relation, 'target') else 'target 없음'}")
                print(f"  - 타입: {relation.type_ if hasattr(relation, 'type_') else 'type_ 없음'}")
        
        # 상속 관계만 필터링해서 확인
        if hasattr(class_graph, 'relations'):
            inheritance_relations = [r for r in class_graph.relations 
                                   if hasattr(r, 'type_') and r.type_ == RelationType.INHERITANCE]
            print(f"\n상속 관계 수: {len(inheritance_relations)}")
            for rel in inheritance_relations:
                print(f"  {rel.source} --|> {rel.target}")

    
    def generate_plantuml(self, class_graph, title: str = "Class Diagram") -> str:
        """ClassGraph를 완전한 PlantUML 다이어그램으로 변환"""
        
        # 디버깅 정보 출력
        # self.debug_class_graph(class_graph)
        
        lines = ["@startuml"]
        lines.append(f"title {title}")
        lines.append("")
        
        # 스타일 설정
        lines.extend([
            "skinparam classFontStyle bold",
            ""
        ])
        
        # 모든 클래스 정의 생성
        if hasattr(class_graph, 'nodes') and class_graph.nodes:
            for node_name, node in class_graph.nodes.items():
                class_def = self._generate_class(node)
                lines.append(class_def)
                lines.append("")
        else:
            lines.append("' No classes found")
            print("경고: 클래스가 발견되지 않았습니다!")
        
        # 모든 관계 정의 생성
        if hasattr(class_graph, 'relations') and class_graph.relations:
            lines.append("' Relationships")
            for relation in class_graph.relations:
                try:
                    rel_def = self._generate_relation(relation)
                    lines.append(rel_def)
                    print(f"관계 추가됨: {rel_def}")  # 디버깅용
                except Exception as e:
                    print(f"관계 생성 실패: {e}, 관계: {relation}")
        else:
            lines.append("' No relationships found")
            print("경고: 관계가 발견되지 않았습니다!")
        
        lines.append("")
        lines.append("@enduml")
        
        return "\n".join(lines)
    
    def save_to_file(self, class_graph, file_path: str, title: str = "Class Diagram"):
        """PlantUML 다이어그램을 파일로 저장"""
        plantuml_content = self.generate_plantuml(class_graph, title)
        
        # 디렉토리가 존재하지 않으면 생성
        directory = os.path.dirname(file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)
        
        # 파일 확장자 확인 및 추가
        if not file_path.endswith('.puml') and not file_path.endswith('.plantuml'):
            file_path += '.puml'
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(plantuml_content)
            print(f"PlantUML 다이어그램이 성공적으로 저장되었습니다: {file_path}")
            return True
        except Exception as e:
            print(f"파일 저장 중 오류 발생: {e}")
            return False
    
    def generate_hierarchical_layout(self, class_graph) -> List[str]:
        """계층적 레이아웃을 위한 추가 지시문 생성"""
        layout_hints = []
        
        # 상속 관계가 있는 경우 계층 구조 힌트 추가
        if hasattr(class_graph, 'relations') and class_graph.relations:
            inheritance_rels = [r for r in class_graph.relations 
                              if r.type_ == RelationType.INHERITANCE]
            if inheritance_rels:
                # 부모 클래스들을 위쪽에 배치
                parents = set(rel.target for rel in inheritance_rels)
                children = set(rel.source for rel in inheritance_rels)
                
                for parent in parents:
                    layout_hints.append(f"!define {parent}_LEVEL 1")
                
                for child in children:
                    layout_hints.append(f"!define {child}_LEVEL 2")
        
        return layout_hints