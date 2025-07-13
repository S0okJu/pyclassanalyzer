import re 

def is_protected(name: str) -> bool:
    return re.fullmatch(r"_([^_]\w*)", name) is not None

def is_private(name: str) -> bool:
    return re.fullmatch(r"__([^_]\w*)", name) is not None and not name.endswith("__")

def is_magic(name: str) -> bool:
    return re.fullmatch(r"__\w+__", name) is not None
