import pytest

@pytest.fixture
def code() -> str:
    return """
    class User:
        def __init__(self, name: str):
            self.name = name
        
        @property
        def age(self) -> int:
            return 20
            
        def get_name(self) -> str:
            return self.name
    """