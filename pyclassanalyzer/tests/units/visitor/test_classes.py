import ast
import pytest
from collections import defaultdict

# --- Stub 및 최소 구조 정의 ---

class StubMemberAnalyzer:
    def __init__(self, result):
        self.result = result
    def analyze_class_members(self, node, class_name):
        # 더미 데이터만 할당
        self.result.class_attributes[class_name] = {}
        self.result.class_methods[class_name] = []

class AnalysisResult:
    def __init__(self):
        self.current_module = "test.module"
        self.class_modules = {}
        self.class_name_to_full = {}
        self.class_attributes = {}
        self.class_methods = {}
        self.inheritance = defaultdict(list)
        self.composition = defaultdict(set)
        self.packages = set(["test"])
        self.project_modules = set(["test.module"])


@pytest.fixture
def result():
    return AnalysisResult()

@pytest.fixture
def visitor(result, monkeypatch):
    from pyclassanalyzer.visitors.classes import ClassVisitor  # 실제 코드 위치에 맞게 수정
    visitor = ClassVisitor(result)
    stub_analyzer = StubMemberAnalyzer(result)
    monkeypatch.setattr(visitor, "member_analyzer", stub_analyzer)
    return visitor

def test_visit_classdef_registers_class(visitor, result):
    # 간단한 클래스 정의
    class_code = "class MyClass:\n    pass"
    node = ast.parse(class_code).body[0]

    visitor.visit_ClassDef(node)

    full_name = "test.module.MyClass"
    # 클래스 등록 확인
    assert full_name in result.class_modules
    assert result.class_name_to_full["MyClass"] == full_name

def test_visit_classdef_handles_duplicate(visitor, result, capsys):
    # 중복 클래스명 상황
    class_code1 = "class MyClass:\n    pass"
    class_code2 = "class MyClass:\n    pass"
    node1 = ast.parse(class_code1).body[0]
    node2 = ast.parse(class_code2).body[0]

    visitor.visit_ClassDef(node1)
    visitor.visit_ClassDef(node2)
    captured = capsys.readouterr()
    assert "Warning: Duplicate class name" in captured.out

def test_visit_classdef_inheritance(visitor, result):
    # 상속 관계 클래스 정의
    class_code = "class Base: pass\nclass Child(Base): pass"
    module = ast.parse(class_code)
    for node in module.body:
        visitor.visit_ClassDef(node)
    child_full = "test.module.Child"
    base_full = "test.module.Base"
    # 상속 관계 확인
    assert base_full in result.inheritance[child_full]

def test_visit_classdef_composition(visitor, result):
    # 조합(컴포지션) 관계 클래스 정의
    class_code = """
class Other: pass
class MyClass:
    def __init__(self):
        self.o = Other()
"""
    module = ast.parse(class_code)
    for node in module.body:
        visitor.visit_ClassDef(node)
    myclass_full = "test.module.MyClass"
    other_full = "test.module.Other"
    # 조합 관계 확인
    assert other_full in result.composition[myclass_full]
