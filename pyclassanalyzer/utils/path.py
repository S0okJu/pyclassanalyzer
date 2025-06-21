
def split_path(path_str: str) -> list[str]:
    
    cleaned = path_str.strip("./")  
    parts = cleaned.split('/')
    
    return [p for p in parts if p]

def find_root_name(path:str) -> str:
    """
    Return last part of path.
    
    ex) ./pyclassanalyzer/tests/units -> units 
    """
    parts = split_path(path)
    return parts[-1]