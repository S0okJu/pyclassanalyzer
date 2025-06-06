from dataclasses import dataclass, field
from typing import Dict, Set, List, Any
from collections import defaultdict

@dataclass
class AnalysisResult:
    """
    This is a data class as a result of analysis and used for making a diagram.
    
    TODO: Refactor this data class to make it more readable and maintainable.
    """
    
    # This used for visitor
    current_class: str = None 
    current_module: str = None

    # {class_name: [inheritance_class_name]}, ex) {User: [UserService, UserRepository]}
    inheritance: Dict[str, List[str]] = field(default_factory=lambda: defaultdict(list))
    # {class_name: [composition_class_name]}, ex) {User: [UserService, UserRepository]}
    composition: Dict[str, Set[str]] = field(default_factory=lambda: defaultdict(set)) 
    # {class_name: module_name}, ex) {User: user.py}
    class_modules: Dict[str, str] = field(default_factory=dict)
    # {class_name: module_name}, ex) {User: user.py}
    class_name_to_full: Dict[str, str] = field(default_factory=dict) 
    
    # import information
    packages: Set[str] = field(default_factory=set)
    external_classes: Set[str] = field(default_factory=set)
    module_to_file: Dict[str, str] = field(default_factory=dict)
    imports: Dict[str, Dict[str, str]] = field(default_factory=lambda: defaultdict(dict))
    project_modules: Set[str] = field(default_factory=set)
    
    # class detail information 
    class_attributes: Dict[str, Dict[str, Any]] = field(default_factory=lambda: defaultdict(dict))
    class_methods: Dict[str, List[Dict[str, Any]]] = field(default_factory=lambda: defaultdict(list)) 
