from abc import *

class Collector(ABC):
    def __init__(self, path: str):
        self.path = path

    @abstractmethod
    def collect(self):
        pass
