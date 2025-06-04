from collections import defaultdict

class ClassRecord:
    def __init__(self, name: str, module: str):
        self.name = name
        self.module = module
    
    @property
    def full_name(self):
        return f"{self.module}.{self.name}" if self.module else self.name

    def __str__(self):
        return self.full_name

    def __repr__(self):
        return f"ClassRecord(name={self.name}, module={self.module}, full_name={self.full_name})"

    
class ClassRecordManager:
    def __init__(self):
        self.records = defaultdict(ClassRecord)

    def add(self, record: ClassRecord):
        # Always save full name to prevent conflict
        # ex) foo.A / bar.A
        self.records[record.full_name] = record

    def get(self, full_name: str):
        return self.records[full_name]
    
    def get_by_name(self, name: str):
        return [record for record in self.records.values() if record.name == name]
    
        