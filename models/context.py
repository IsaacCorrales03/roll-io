class ActionResult:
    def __init__(self, success: bool, effects: list):
        self.success = success
        self.effects = effects

class Context:
    def __init__(self):
        self.campaign = None
        self.log = []

    def roll_d20(self) -> int:
        import random
        return random.randint(1, 20)

    def add_log(self, entry: dict):
        self.log.append(entry)
