class Rectangle:
    def __init__(self, length: int, width: int):
        self.length = length
        self.width = width

    def __iter__(self):
        yield {"length": self.length}
        yield {"width": self.width}


# Option B — Explicit iterator object (reference only)
class RectangleIterator:
    def __init__(self, rectangle):
        self.rect = rectangle
        self.index = 0

    def __iter__(self):
        return self

    def __next__(self):
        if self.index == 0:
            self.index += 1
            return {"length": self.rect.length}
        elif self.index == 1:
            self.index += 1
            return {"width": self.rect.width}
        raise StopIteration


class RectangleExplicit:
    def __init__(self, length: int, width: int):
        self.length = length
        self.width = width

    def __iter__(self):
        return RectangleIterator(self)
