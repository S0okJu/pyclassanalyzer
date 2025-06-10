from unittest.mock import MagicMock
import pytest


class TestClassVisitor:
    def setup_method(self):
        self.member_analyzer = MagicMock()
    
    def test_visit_ClassDef(self):
        pass 