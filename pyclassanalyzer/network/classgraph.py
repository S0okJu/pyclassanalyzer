from typing import Optional, List, Dict, Set
from enum import Enum

from pydantic import BaseModel

class ModuleType(Enum):
    INTERNAL = "internal"
    EXTERNAL = "external"
    
    def __str__(self):
        return self.value
    
    def is_internal(self):
        return self == ModuleType.INTERNAL

class RelationType(Enum):
    INHERITANCE = "inheritance"
    COMPOSITION = "composition"
    USE = "use"
    
    def __str__(self):
        return self.value
        

class ModuleDef(BaseModel):
    name: str
    type_: Optional[ModuleType] = None
    
class FunctionDef(BaseModel):
    name: str 
    fields: Optional[List[str]] = []
    
        
class ClassNode(BaseModel):
    module: Optional[ModuleDef] = None
    external_module: List[ModuleDef] = []

    annotations: Optional[List[str]] = []

    name: str
    attributes: Optional[List[str]] = []
    functions: Optional[List[FunctionDef]] = []
 
    def add_function(self, func: FunctionDef):
        self.functions.append(func)
    
    def add_attribute(self, attr: str):
        self.attributes.append(attr)   
    
 
    def __hash__(self) -> int:
        return hash(self.name)
    
    def __eq__(self, other: object) -> bool:
        if isinstance(other, ClassNode):
            return self.name == other.name
        return False
    
    
    

class Relation(BaseModel):        
    source: str
    target: str
    
    type_:RelationType
    
    def __hash__(self) -> int: 
        return hash((self.type_, self.source, self.target))
    
    def __eq__(self, other: object) -> bool:
        if isinstance(other, Relation):
            return (self.type_ == other.type_ and 
                   self.source == other.source and 
                   self.target == other.target)
        return False

class ClassGraph(BaseModel):
    nodes: Dict[str, ClassNode] = {}
    relations: List[Relation] = []

    def add_node(self, node: ClassNode):
        self.nodes[node.name] = node
    
    def remove_node(self, name:str) -> bool:
        if name not in self.nodes:
            return False
        
        # Delete related relations
        self.relations =[rel for rel in self.relations 
                         if rel.source != name and rel.target != name]
        del self.nodes[name]
        return True 

    def add_relation(self, relation: Relation) -> bool:
        
        if relation.source not in self.nodes or relation.target not in self.nodes:
            return False
        
        # Check duplication
        if relation not in self.relations:
            self.relations.append(relation)
            return True
        return False
    
    def remove_relation(self, relation: Relation) -> bool:
        if relation in self.relations:
            self.relations.remove(relation)
            return True
        return False

    def get_relations_by_type(self, relation_type: RelationType) -> List[Relation]:
        """특정 타입의 관계들을 반환합니다."""
        return [rel for rel in self.relations if rel.type_ == relation_type]
    
    def get_node(self, name:str) -> Optional[ClassNode]:
        return self.nodes.get(name)

    def get_outgoing_rels(self, name:str) -> List[Relation]:
        return [rel for rel in self.relations 
                if rel.source == name]

    def get_incoming_rels(self, name:str) -> List[Relation]:
        return [rel for rel in self.relations 
                if rel.target == name]
    
    def get_neighbors(self, name: str) -> Set[str]:
        neighbors = set()
        for rel in self.relations:
            if rel.source == name:
                neighbors.add(rel.target)
            elif rel.target == name:
                neighbors.add(rel.source)
        return neighbors
    
    def get_descendants(self, name:str) -> Set[str]:
        descendants = set()
        visited = set()
        
        def dfs(current:str):
            if current in visited:
                return 
            visited.add(current)
            
            for rel in self.get_outgoing_rels(current):
                descendants.add(rel.target)
                dfs(rel.target)
        
        dfs(name)
        return descendants
    
    def get_ancestors(self, name:str) -> Set[str]:
        ancestors = set()
        visited = set()
        
        def dfs(current:str):
            if current in visited:
                return 
            visited.add(current)
            
            for rel in self.get_incoming_rels(current):
                ancestors.add(rel.source)
                dfs(rel.source)
        
        dfs(name)
        return ancestors
    
    def has_cycle(self) -> bool:
        visited = set()
        stack = set()
        
        def dfs(node: str) -> bool:
            visited.add(node)
            stack.add(node)
            
            for rel in self.get_outgoing_rels(node):
                if rel.target not in visited:
                    if dfs(rel.target):
                        return True
                elif rel.target in stack:
                    return True
            
            stack.remove(node)
            return False
        
        for node in self.nodes:
            if node not in visited:
                if dfs(node):
                    return True
        return False
    
    def topological_sort(self) -> Optional[List[str]]:
        """
        위상 정렬 
        """
        if self.has_cycle():
            return None
        
        visited = set()
        stack = []
        
        def dfs(node: str):
            visited.add(node)
            for rel in self.get_outgoing_relations(node):
                if rel.target not in visited:
                    dfs(rel.target)
            stack.append(node)
        
        for node_name in self.nodes:
            if node_name not in visited:
                dfs(node_name)
        
        return stack[::-1]
    
        

        

        
    
