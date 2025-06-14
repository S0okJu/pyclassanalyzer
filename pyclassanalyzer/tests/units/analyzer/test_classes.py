import pytest
import os
import ast
import tempfile
import shutil

from pyclassanalyzer.analyzer.classes import ClassAnalyzer

class DummyImportVisitor:
    def __init__(self, result):
        self.called = False
    def visit(self, tree):
        self.called = True

class DummyClassVisitor:
    def __init__(self, result):
        self.called = False
    def visit(self, tree):
        self.called = True

class DummyMemberAnalyzer:
    def __init__(self, result):
        pass

class DummyPlantUMLGenerator:
    def __init__(self, result):
        pass

class DummyAnalysisResult:
    def __init__(self):
        self.current_module = None
        self.class_modules = {}
        self.class_name_to_full = {}
        self.module_to_file = {}
        self.project_modules = set()
        self.packages = set()

@pytest.fixture
def analyzer(monkeypatch):
    analyzer = ClassAnalyzer()
    
    analyzer.result = DummyAnalysisResult()
    analyzer.import_visitor = DummyImportVisitor(analyzer.result)
    analyzer.class_visitor = DummyClassVisitor(analyzer.result)
    analyzer.member_analyzer = DummyMemberAnalyzer(analyzer.result)
    analyzer.plantuml_generator = DummyPlantUMLGenerator(analyzer.result)
    
    return analyzer

@pytest.fixture
def package_test_exist_case(tmp_path):
    # mypkg 패키지 생성
    pkg_dir = tmp_path / "mypkg"
    pkg_dir.mkdir()
    (pkg_dir / "__init__.py").write_text("", encoding="utf-8")
    (pkg_dir / "a.py").write_text("class A: pass", encoding="utf-8")
    (pkg_dir / "b.py").write_text("class B: pass", encoding="utf-8")

    # tests 패키지 및 하위 패키지 생성
    test_pkg_dir = tmp_path / "tests"
    test_pkg_dir.mkdir()
    (test_pkg_dir / "__init__.py").write_text("", encoding="utf-8")
    (test_pkg_dir / "test_a.py").write_text("class TestA: pass", encoding="utf-8")

    test_subpackage = test_pkg_dir / "units"
    test_subpackage.mkdir()
    (test_subpackage / "__init__.py").write_text("", encoding="utf-8")
    (test_subpackage / "test_b.py").write_text("class TestB: pass", encoding="utf-8")

    return tmp_path

def test_analyze_file_sets_current_module_and_visits(tmp_path, analyzer):
    # 임시 파이썬 파일 생성
    code = "class Foo:\n    pass"
    file_path = tmp_path / "foo.py"
    file_path.write_text(code, encoding="utf-8")

    analyzer.analyze_file(str(file_path))

    assert analyzer.result.current_module == "foo"
    assert analyzer.import_visitor.called
    assert analyzer.class_visitor.called

def test_analyze_file_handles_file_not_found(analyzer, capsys):
    analyzer.analyze_file("not_exist.py")
    captured = capsys.readouterr()
    assert "Error analyzing file not_exist.py:" in captured.out

def test_analyze_directory_collects_classes_and_modules(tmp_path, analyzer):
    # 임시 디렉토리 구조 및 파일 생성
    pkg_dir = tmp_path / "mypkg"
    pkg_dir.mkdir()
    (pkg_dir / "__init__.py").write_text("", encoding="utf-8")
    (pkg_dir / "a.py").write_text("class A: pass", encoding="utf-8")
    (pkg_dir / "b.py").write_text("class B: pass", encoding="utf-8")

    analyzer.analyze_directory(str(tmp_path))

    # 패키지 및 모듈 정보가 수집되었는지 확인
    assert "mypkg" in analyzer.result.packages
    assert "mypkg.a" in analyzer.result.project_modules
    assert "mypkg.b" in analyzer.result.project_modules
    
    # 클래스명도 수집되었는지 확인 (첫 번째 패스에서)
    assert "mypkg.a.A" in analyzer.result.class_modules
    assert "mypkg.b.B" in analyzer.result.class_modules

def test_analyze_directory_handles_syntax_error(tmp_path, analyzer, capsys):
    # 문법 오류가 있는 파일 생성
    (tmp_path / "bad.py").write_text("class Oops(:\n    pass", encoding="utf-8")
    analyzer.analyze_directory(str(tmp_path))
    captured = capsys.readouterr()
    assert "Error in first pass for" in captured.out or "Error in second pass for" in captured.out

def test_analyze_directory_no_test_true(package_test_exist_case, analyzer):
    analyzer.analyze_directory(str(package_test_exist_case), no_test=True)
    
    assert 'mypkg.a.A' in analyzer.result.class_modules
    assert 'mypkg.b.B' in analyzer.result.class_modules
    
    assert 'tests.test_a.TestA' not in analyzer.result.class_modules
    assert 'tests.units.test_b.TestB' not in analyzer.result.class_modules
    
def test_analyze_directory_no_test_false(package_test_exist_case,analyzer):
    analyzer.analyze_directory(str(package_test_exist_case), no_test=False)
    
    assert 'mypkg.a.A' in analyzer.result.class_modules
    assert 'mypkg.b.B' in analyzer.result.class_modules
    
    assert 'tests.test_a.TestA' in analyzer.result.class_modules
    assert 'tests.units.test_b.TestB' in analyzer.result.class_modules

def test__collect_project_structure_success_no_test_true(package_test_exist_case, analyzer):
    
    analyzer._collect_project_structure(str(package_test_exist_case), no_test=True)
    
    assert 'mypkg' in analyzer.result.packages
    assert 'tests' not in analyzer.result.packages
    assert 'tests.units' not in analyzer.result.packages
    
def test__collect_project_structure_success_no_test_false(package_test_exist_case, analyzer):
    
    analyzer._collect_project_structure(str(package_test_exist_case), no_test=False)
        
    assert 'mypkg' in analyzer.result.packages    
    assert 'tests' in analyzer.result.packages
    assert 'tests.units' in analyzer.result.packages
    