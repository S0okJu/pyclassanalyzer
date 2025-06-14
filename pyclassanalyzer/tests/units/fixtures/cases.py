import ast

class OnlyClassNodeCase:
    def __init__(self) -> None:
        self.code = """
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
    
    def run(self):
        return ast.parse(self.code).body
    