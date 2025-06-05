from dataclasses import dataclass, field
from typing import Dict, Set

@dataclass
class ModuleInfo:
    name: str
    file_path: str
    imports: Dict[str, str] = field(default_factory=dict)  # alias -> full_name
    classes: Set[str] = field(default_factory=set)  # class names in this module

    def add_import(self, alias: str, full_name: str):
        self.imports[alias] = full_name

    def add_class(self, class_name: str):
        self.classes.add(class_name)

    @property
    def is_package(self) -> bool:
        return self.name.endswith('__init__') 