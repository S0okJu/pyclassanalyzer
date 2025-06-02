from pyclass_analyzer.collector.collector import FileCollector
from pyclass_analyzer.parser.parser import ProjectParser
from pyclass_analyzer.types.result import Result

class Analyzer:
    def __init__(self, path: str):
        self.path = path
        self.result = Result()

    def analyze(self):
        collector = FileCollector(self.path)
        file_info = collector.collect()
        
        parser = ProjectParser(file_info, self.result)
        parser.parse()