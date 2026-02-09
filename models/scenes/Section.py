from dataclasses import dataclass

@dataclass
class Section:
    id: str        # a1, a2, b1...
    fog: bool = True
