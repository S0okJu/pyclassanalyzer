from b import B

class C(B):
    def __init__(self):
        super().__init__()
        self.world = "world"
