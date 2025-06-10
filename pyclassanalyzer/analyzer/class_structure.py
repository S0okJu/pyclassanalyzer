import ast
import os
from typing import Dict, Set, List

from pyclassanalyzer.types import AnalysisResult
from pyclassanalyzer.visitors import ImportVisitor, ClassVisitor
from .member import MemberAnalyzer
from pyclassanalyzer.generators import PlantUMLGenerator

class ClassAnalyzer:
    """Python 클래스 구조 분석기"""
    
    def __init__(self):
        self.result = AnalysisResult()
        self.import_visitor = ImportVisitor(self.result)
        self.class_visitor = ClassVisitor(self.result)
        self.member_analyzer = MemberAnalyzer(self.result)
        self.plantuml_generator = PlantUMLGenerator(self.result)

    def analyze_file(self, file_path: str) -> None:
        """파일 분석"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            module_name = os.path.splitext(os.path.basename(file_path))[0]
            self.result.current_module = module_name
            
            # import 분석
            self.import_visitor.visit(tree)
            
            # 클래스 분석
            self.class_visitor.visit(tree)
            
        except Exception as e:
            print(f"Error analyzing file {file_path}: {e}")

    def analyze_directory(self, path: str) -> None:
        """디렉토리 분석"""
        self._collect_project_structure(path)
        all_files = []
        for root, _, files in os.walk(path):
            for file in files:
                if file.endswith('.py'):
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, path)
                    module_path_without_ext = os.path.splitext(rel_path)[0]
                    module_path = module_path_without_ext.replace(os.path.sep, ".")
                    all_files.append((full_path, module_path, file))
        # 1차 패스: 모든 클래스의 full name을 미리 수집
        for full_path, module_path, file in all_files:
            self.result.module_to_file[module_path] = file
            self.result.project_modules.add(module_path)
            with open(full_path, 'r', encoding='utf-8') as f:
                try:
                    tree = ast.parse(f.read(), filename=file)
                    self.result.current_module = module_path
                    for node in ast.walk(tree):
                        if isinstance(node, ast.ClassDef):
                            class_name = f"{module_path}.{node.name}"
                            self.result.class_modules[class_name] = module_path
                            # 단순명 중복 방지: 이미 있으면 덮어쓰지 않음
                            if node.name not in self.result.class_name_to_full:
                                self.result.class_name_to_full[node.name] = class_name
                            else:
                                print(f"[WARNING] Duplicate class name '{node.name}' found. Existing: {self.result.class_name_to_full[node.name]}, New: {class_name} (IGNORED)")
                except Exception as e:
                    print(f"Error in first pass for {full_path}: {e}")
                    continue
        # 2차 패스: 관계 분석 (full name만 사용)
        for full_path, module_path, file in all_files:
            with open(full_path, 'r', encoding='utf-8') as f:
                try:
                    tree = ast.parse(f.read(), filename=file)
                    self.result.current_module = module_path
                    self.import_visitor.visit(tree)
                    self.class_visitor.visit(tree)
                except Exception as e:
                    print(f"Error in second pass for {full_path}: {e}")
                    continue
        self.result.current_module = None

    def _collect_project_structure(self, path: str) -> None:
        """프로젝트 구조 수집"""
        # 패키지 정보 수집
        for root, dirs, files in os.walk(path):
            if '__init__.py' in files:
                rel_path = os.path.relpath(root, path)
                pkg = rel_path.replace(os.path.sep, ".") if rel_path != '.' else ''
                if pkg:
                    self.result.packages.add(pkg)
        
        # 최상위 디렉토리명도 패키지로 간주 (일반적인 프로젝트 구조)
        project_root_name = os.path.basename(os.path.abspath(path))
        if project_root_name and project_root_name != '.':
            self.result.packages.add(project_root_name)

    def generate_diagram(self, output_file: str = "class_diagram.puml", include_attributes: bool = True, include_methods: bool = True) -> None:
        """PlantUML 다이어그램 생성"""
        self.plantuml_generator.generate_diagram(output_file, include_attributes, include_methods)

    def get_class_info(self, class_name: str) -> Dict:
        """클래스 정보 조회"""
        return {
            'attributes': self.result.class_attributes.get(class_name, {}),
            'methods': self.result.class_methods.get(class_name, []),
            'inheritance': self.result.inheritance.get(class_name, []),
            'composition': list(self.result.composition.get(class_name, set()))
        }

    def get_all_classes(self) -> List[str]:
        """모든 클래스 목록 조회"""
        return list(self.result.class_modules.keys())

    def get_inheritance_tree(self) -> Dict[str, List[str]]:
        """상속 트리 조회"""
        return dict(self.result.inheritance)

    def get_composition_relationships(self) -> Dict[str, Set[str]]:
        """조합 관계 조회"""
        return dict(self.result.composition)

    def print_analysis_summary(self) -> None:
        """분석 결과 요약 출력"""
        print("\n=== 분석 결과 요약 ===")
        print(f"발견된 패키지 수: {len(self.result.packages)}")
        print(f"발견된 클래스 수: {len(self.result.class_modules)}")
        print(f"외부 클래스 수: {len(self.result.external_classes)}")
        print(f"상속 관계 수: {sum(len(parents) for parents in self.result.inheritance.values())}")
        print(f"조합 관계 수: {sum(len(members) for members in self.result.composition.values())}")
        
        # 속성 통계
        total_attributes = sum(len(attrs) for attrs in self.result.class_attributes.values())
        total_methods = sum(len(methods) for methods in self.result.class_methods.values())
        print(f"총 속성 수: {total_attributes}")
        print(f"총 메서드 수: {total_methods}")
        
        print("\n패키지 목록:")
        for pkg in sorted(self.result.packages):
            print(f"  - {pkg}")
        
        print("\n외부 클래스 목록:")
        for ext_cls in sorted(self.result.external_classes):
            print(f"  - {ext_cls}")
        
        # 클래스별 속성 상세 정보
        print("\n클래스별 속성 정보:")
        for cls_name, attributes in self.result.class_attributes.items():
            if attributes:
                simple_name = cls_name.split('.')[-1]
                print(f"  {simple_name}:")
                for attr_name, attr_info in attributes.items():
                    print(f"    - {attr_name} ({attr_info['type']}, {attr_info['visibility']}, {attr_info['data_type']})") 