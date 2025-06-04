from pyclass_analyzer.parser.parser import ProjectParser
from pyclass_analyzer.types.result import Result
from pyclass_analyzer.collector.manager import CollectorManager

class Analyzer:
    def __init__(self, path: str):
        self.path = path

    def analyze(self) -> Result:
        
        collector_manager = CollectorManager(self.path)
        result = collector_manager.collect()
        
        parser = ProjectParser(result = result)
        parser_result = parser.parse()
        
        return parser_result