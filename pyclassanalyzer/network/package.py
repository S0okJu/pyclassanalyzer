import ast
import os 

from typing import Optional, Dict, List, Generator, Tuple
from pydantic import BaseModel, Field

from pyclassanalyzer.utils.path import split_path


PACKAGE = "package"
MODULE = "module"

class Package(BaseModel):
    name: str 
    type_: Optional[str] = ""
    
    def __eq__(self, other) -> bool:
        return self.name == other.name and self.type_ == other.type_


class PackageNode(BaseModel):
    value: Package
    childs: Optional[Dict[str, "PackageNode"]] = Field(default_factory=dict)

    def _add_child(self, name:str, type_: str):
        if name in self.childs:
            raise ValueError(f"Child with name {name} already exists")
        self.childs[name] = PackageNode(value=Package(name=name, type_=type_))
    
    def get_child(self, name:str) -> Optional["PackageNode"]:
        return self.childs.get(name)
    
    def create_child(self, name:str, type_: str) -> "PackageNode":
        
        child = self.get_child(name)
        if child is None:
            self._add_child(name, type_)
            child = self.get_child(name)
        
        return child 

class PackageTree:
    def __init__(self, root: str) -> None:
        self.root = PackageNode(value=Package(name=root, type_=PACKAGE))
    
    def build(self, paths: List[str], base_path: str):
        """
        path는 무조건 절대 경로로 받는다.
        순회하면서 상대 경로로 변환한다. 
        """
        for path in paths:
            # 상대 경로로 변경하기
            path = os.path.abspath(path)
            rel_path = os.path.relpath(path, base_path)
            parts = split_path(rel_path)
            current = self.root
            
            
            parts_len = len(parts) -1 
            for i, part in enumerate(parts):
                type_ = MODULE if i == parts_len and '.' in part else PACKAGE
                
                current = current.create_child(name=part, type_=type_)
    
    def traverse(self, base_path: str, excludes:List[str]) -> Generator[Tuple[str, ast.AST], None, None]:

        def _dfs(node: PackageNode, path: List[str]):
            current_path = path + [node.value.name]

            if node.value.type_ == PACKAGE and node.value.name in excludes:
                return
            
            if node.value.type_ == MODULE:
                                
                full_path = os.path.join(base_path, *current_path[1:])

                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    tree = ast.parse(content)
                    yield full_path, tree

            for child in node.childs.values():
                yield from _dfs(child, current_path)

        yield from _dfs(self.root, [])
            
    
            
            
        
    

        
    
    

    