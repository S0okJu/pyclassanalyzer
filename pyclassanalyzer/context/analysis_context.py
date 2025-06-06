from dataclasses import dataclass, field
from typing import Dict, Set, List, Any
from collections import defaultdict

@dataclass
class AnalysisContext:
    """분석 컨텍스트를 저장하는 데이터 클래스"""
    current_class: str = None
    current_module: str = None
    inheritance: Dict[str, List[str]] = field(default_factory=lambda: defaultdict(list))
    composition: Dict[str, Set[str]] = field(default_factory=lambda: defaultdict(set))
    class_modules: Dict[str, str] = field(default_factory=dict)
    class_name_to_full: Dict[str, str] = field(default_factory=dict)
    packages: Set[str] = field(default_factory=set)
    external_classes: Set[str] = field(default_factory=set)
    module_to_file: Dict[str, str] = field(default_factory=dict)
    imports: Dict[str, Dict[str, str]] = field(default_factory=lambda: defaultdict(dict))
    project_modules: Set[str] = field(default_factory=set)
    class_attributes: Dict[str, Dict[str, Any]] = field(default_factory=lambda: defaultdict(dict))
    class_methods: Dict[str, List[Dict[str, Any]]] = field(default_factory=lambda: defaultdict(list)) 