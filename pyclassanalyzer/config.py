import toml

from typing import Dict, Any, Optional
from pathlib import Path

def find_config_pathlib() -> Optional[Path]:
    config_path = Path.cwd() / "config.toml"
    return config_path

class TomlConfig:
    
    def __init__(self) -> None:
        self.path = find_config_pathlib()
        self.data:Dict[str,Any] = {}
        self._load()
    
    
    def _load(self) -> None:
        with open(self.path, 'r', encoding='utf-8') as f:
            self.data = toml.load(f)
    
    def get(self, key:str) -> Dict[str,Any]:
        """Split by . 

        Args:
            key (str): _description_

        Returns:
            Dict[str,Any]: _description_
        """
        keys = key.split('.')
        current = self.data
        
        try:
            for k in keys:
                current = current[k]
            return current
        except (KeyError, TypeError):
            print(f"Key error when parsing toml")
            return {}
    
        
            
    
    