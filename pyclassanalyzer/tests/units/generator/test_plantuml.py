import pytest
from io import StringIO

from pyclassanalyzer.generators.plantuml_generator import PlantUMLGenerator

class UnclosableStringIO(StringIO):
    def close(self):
        # close를 무시해서 닫히지 않게 함
        pass

@pytest.fixture
def dummy_result():
    # 최소 AnalysisResult 구조
    class DummyResult:
        def __init__(self):
            self.class_modules = {
                "pkg.A": "pkg",
                "pkg.B": "pkg",
                "pkg2.C": "pkg2"
            }
            self.module_to_file = {
                "pkg": "a.py",
                "pkg2": "c.py"
            }
            self.class_attributes = {
                "pkg.A": {
                    "x": {"type": "class_variable", "data_type": "int", "visibility": "public", "line": 2}
                },
                "pkg.B": {},
                "pkg2.C": {}
            }
            self.class_methods = {
                "pkg.A": [
                    {"name": "__init__", "visibility": "public", "decorators": None, "is_property": False, "line": 2, "params": ["x"]}
                ],
                "pkg.B": [
                    {"name": "foo", "visibility": "protected", "decorators": None, "is_property": False, "line": 3, "params": []}
                ],
                "pkg2.C": []
            }
            self.inheritance = {
                "pkg.B": ["pkg.A"]
            }
            self.composition = {
                "pkg.A": set(),
                "pkg.B": {"pkg2.C"},
                "pkg2.C": set()
            }
    return DummyResult()

@pytest.fixture
def generator(dummy_result):
    return PlantUMLGenerator(dummy_result)

def test_generate_diagram_output(generator, monkeypatch):
    output = UnclosableStringIO()
    monkeypatch.setattr("builtins.open", lambda *args, **kwargs: output)

    generator.generate_diagram(output_file="dummy.puml", include_attributes=True, include_methods=True)
    result = output.getvalue()

    # 헤더/푸터 포함 여부
    assert "@startuml" in result
    assert "@enduml" in result

    # 클래스 정의가 포함되어 있는지
    assert 'class pkg.A as "A"' in result
    assert 'class pkg.B as "B"' in result
    assert 'class pkg2.C as "C"' in result

    # 속성/메서드가 올바르게 출력되는지
    assert "+x: int" in result
    assert "+__init__()" in result
    assert "#foo()" in result

    # 상속/조합 관계가 올바르게 출력되는지
    assert "pkg.A <|-- pkg.B" in result
    assert "pkg.B --> pkg2.C : has-a" in result

def test_generate_diagram_excludes_attributes_methods(generator, monkeypatch):
    output = UnclosableStringIO()
    monkeypatch.setattr("builtins.open", lambda *args, **kwargs: output)

    generator.generate_diagram(output_file="dummy.puml", include_attributes=False, include_methods=False)
    result = output.getvalue()

    # 속성/메서드가 출력되지 않아야 함
    assert "+x: int" not in result
    assert "+__init__(x)" not in result
    assert "#foo()" not in result

def test_format_attribute(generator):
    attr_info = {"type": "class_variable", "data_type": "int", "visibility": "protected", "line": 1}
    result = generator._format_attribute("value", attr_info)
    assert result == "#value: int"

def test_format_method(generator):
    method_info = {"name": "foo", "visibility": "private", "decorators": None, "is_property": False, "line": 1, "params": ["a", "b"]}
    result = generator._format_method(method_info)
    assert result == "-foo(a, b)"

    # 특수 메서드
    method_info = {"name": "__init__", "visibility": "public", "decorators": None, "is_property": False, "line": 1, "params": ["self", "x"]}
    result = generator._format_method(method_info)
    assert result == "+__init__()"

    # 프로퍼티는 None 반환
    method_info = {"name": "prop", "visibility": "public", "decorators": None, "is_property": True, "line": 1, "params": []}
    result = generator._format_method(method_info)
    assert result is None
