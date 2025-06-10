import ast
import pytest

from pyclassanalyzer.analyzer.member import MemberAnalyzer
from pyclassanalyzer.types import AnalysisResult


@pytest.fixture
def sample_class_ast():
    """Fixture providing parsed AST for a test class"""
    code = """
class SampleClass:
    class_var = 42
    
    def __init__(self):
        self.instance_var = "test"
        self._protected_var = 123
        self.__private_var = True
        
    @property
    def my_property(self):
        return self._protected_var
        
    def my_method(self, param: int):
        self.dynamic_var = [1, 2, 3]
    """
    return ast.parse(code).body[0]

@pytest.fixture
def analysis_result():
    """Fixture providing clean AnalysisResult instance"""
    return AnalysisResult()

@pytest.fixture
def analyzer(analysis_result):
    """Fixture providing initialized MemberAnalyzer"""
    return MemberAnalyzer(analysis_result)

def test_class_variable_analysis(analyzer, sample_class_ast, analysis_result):
    """Test class-level variable detection"""
    analyzer.analyze_class_members(sample_class_ast, 'SampleClass')
    attrs = analysis_result.class_attributes['SampleClass']
    
    assert attrs['class_var'] == {
        'type': 'class_variable',
        'data_type': 'int',
        'visibility': 'public',
        'line': 3
    }

def test_instance_variable_analysis(analyzer, sample_class_ast, analysis_result):
    """Test __init__ method instance variable detection"""
    analyzer.analyze_class_members(sample_class_ast, 'SampleClass')
    attrs = analysis_result.class_attributes['SampleClass']
    
    assert attrs['instance_var'] == {
        'type': 'instance_variable',
        'data_type': 'str',
        'visibility': 'public',
        'line': 6
    }

def test_property_analysis(analyzer, sample_class_ast, analysis_result):
    """Test @property detection and attribute creation"""
    analyzer.analyze_class_members(sample_class_ast, 'SampleClass')
    attrs = analysis_result.class_attributes['SampleClass']
    methods = analysis_result.class_methods['SampleClass']
    
    assert attrs['my_property']['type'] == 'property'
    assert any(m['name'] == 'my_property' and m['is_property'] for m in methods)

def test_dynamic_attribute_analysis(analyzer, sample_class_ast, analysis_result):
    """Test dynamically created attributes in methods"""
    analyzer.analyze_class_members(sample_class_ast, 'SampleClass')
    attrs = analysis_result.class_attributes['SampleClass']
    
    assert attrs['dynamic_var'] == {
        'type': 'dynamic_attribute',
        'data_type': 'list',
        'visibility': 'public',
        'line': 15,
        'method': 'my_method'
    }

def test_visibility_modifiers(analyzer, sample_class_ast, analysis_result):
    """Test visibility modifier detection"""
    analyzer.analyze_class_members(sample_class_ast, 'SampleClass')
    attrs = analysis_result.class_attributes['SampleClass']
    
    assert attrs['_protected_var']['visibility'] == 'protected'
    assert attrs['__private_var']['visibility'] == 'private'

def test_method_parameter_analysis(analyzer, sample_class_ast, analysis_result):
    """Test method parameter extraction"""
    analyzer.analyze_class_members(sample_class_ast, 'SampleClass')
    methods = analysis_result.class_methods['SampleClass']
    
    my_method = next(m for m in methods if m['name'] == 'my_method')
    assert my_method['params'] == ['param']
