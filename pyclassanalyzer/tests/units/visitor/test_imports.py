import pytest
import ast
from pyclassanalyzer.visitors.imports import ImportVisitor

from pyclassanalyzer.types import AnalysisResult

class MockResult(AnalysisResult):
    def __init__(self):
        super().__init__()
        self.project_modules = (
            'test1',
            'test2'
        )

class MockImportVisitor(ImportVisitor):
    def __init__(self, result):
        super().__init__(result)



@pytest.fixture
def fake_nodes():
    code = """
import os, sys
from collections import defaultdict, namedtuple
from .test1 import local_class as helloworld
from .test2 import local_class2, local_class3

    """
    return ast.parse(code).body


class TestImportVisitor:
    def setup_method(self):
        result = MockResult()
        result.imports["test_module"] = {}
        self.visitor = MockImportVisitor(result)
        self.visitor.current_module = "test_module"

    def test__is_internal_module_success(self):
        assert self.visitor._is_internal_module(".") is True
        assert self.visitor._is_internal_module(".base") is True
        assert self.visitor._is_internal_module(".os") is True  
        
        assert self.visitor._is_internal_module("os") is False 
        assert self.visitor._is_internal_module("sys") is False

    def test_visit_imports(self, fake_nodes):
        for node in fake_nodes:
            self.visitor.visit(node)

        imports = self.visitor.result.imports["test_module"]
        assert imports["os"] == "os"
        assert imports["sys"] == "sys"
        assert imports["defaultdict"] == "collections.defaultdict"
        assert imports["namedtuple"] == "collections.namedtuple"
        assert imports["helloworld"] == "test1.local_class"
        assert imports["local_class2"] == "test2.local_class2"
        assert imports["local_class3"] == "test2.local_class3"

    def test_external_class_detection(self, fake_nodes):
        for node in fake_nodes:
            self.visitor.visit(node)

        external = self.visitor.result.external_classes
        print(external)
        assert "defaultdict" in external
        assert "namedtuple" in external
        
        assert "helloworld" not in external
        assert "local_class2" not in external
