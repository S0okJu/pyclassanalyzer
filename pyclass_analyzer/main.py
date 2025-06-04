from pyclass_analyzer.analyzer import Analyzer
from pyclass_analyzer.exporter.exporter import PlantUMLExporter
from pyclass_analyzer.config.config import Config

if __name__ == "__main__":
    analyzer = Analyzer("./pyclass_analyzer")
    result = analyzer.analyze() 
    
    config = Config()
    exporter = PlantUMLExporter(config, result)
    exporter.export("pyclass-analyzer.puml")