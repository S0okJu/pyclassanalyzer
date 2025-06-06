import ast
from pyclassanalyzer.analyzers import MemberAnalyzer
from pyclassanalyzer.types import AnalysisResult

    
class TestMemberAnalyzer:
    
    def setup_method(self):
        self.result = AnalysisResult()
        self.analyzer = MemberAnalyzer(self.result)

    def test__process_class_attribute_success(self):
        code = '''
class Foo:
    bar = 123
'''
        self.analyze(code, "Foo")
        attrs = self.result.class_attributes["Foo"]
        assert "bar" in attrs
    
    
    
    def analyze(self, code: str, class_name: str):
        tree = ast.parse(code)
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == class_name:
                self.analyzer.analyze_class_members(node, class_name)
                return

    def test_class_and_instance_attributes(self):
        code = '''
class Foo:
    bar = 123
    def __init__(self):
        self.baz = "hello"
'''
        self.analyze(code, "Foo")
        attrs = self.result.class_attributes["Foo"]
        assert "bar" in attrs
        assert attrs["bar"]["type"] == "class_variable"
        assert "baz" in attrs
        assert attrs["baz"]["type"] == "instance_variable"

    def test_method_and_property(self):
        code = '''
class Bar:
    @property
    def name(self):
        return "bar"
    def hello(self, x):
        return x
'''
        self.analyze(code, "Bar")
        methods = self.result.class_methods["Bar"]
        method_names = [m["name"] for m in methods]
        assert "name" in method_names
        assert "hello" in method_names
        attrs = self.result.class_attributes["Bar"]
        assert "name" in attrs
        assert attrs["name"]["type"] == "property"

    def test_dynamic_attribute(self):
        code = '''
class Baz:
    def foo(self):
        self.x = 1
        self.y = "hi"
'''
        self.analyze(code, "Baz")
        attrs = self.result.class_attributes["Baz"]
        assert "x" in attrs
        assert attrs["x"]["type"] == "dynamic_attribute"
        assert "y" in attrs
        assert attrs["y"]["data_type"] == "str"