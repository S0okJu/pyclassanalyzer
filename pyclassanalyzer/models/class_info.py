from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional

@dataclass
class AttributeInfo:
    name: str
    type: str  # class_variable, instance_variable, dynamic_attribute, property
    data_type: str
    visibility: str  # public, protected, private
    line: int
    method: Optional[str] = None  # for dynamic attributes

@dataclass
class MethodInfo:
    name: str
    visibility: str
    decorators: List[str]
    is_property: bool
    line: int
    params: List[str]

@dataclass
class ClassInfo:
    name: str
    module: str
    bases: List[str] = field(default_factory=list)
    attributes: Dict[str, AttributeInfo] = field(default_factory=dict)
    methods: List[MethodInfo] = field(default_factory=list)
    composition: Set[str] = field(default_factory=set)
    is_external: bool = False

    @property
    def simple_name(self) -> str:
        return self.name.split('.')[-1]

    def add_attribute(self, attr_info: AttributeInfo):
        self.attributes[attr_info.name] = attr_info

    def add_method(self, method_info: MethodInfo):
        self.methods.append(method_info)

    def add_base(self, base: str):
        if base not in self.bases:
            self.bases.append(base)

    def add_composition(self, member: str):
        self.composition.add(member) 