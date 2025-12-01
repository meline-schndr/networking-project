class SharedContext:
    def __init__(self):
        self.stats = None
        self.prod_manager = None

class PizzeriaStats:
    def __init__(self):
        self.accepted_orders = 0
        self.refused_orders = 0
        self.ingredients = {'R': 0, 'J': 0, 'V': 0, 'B': 0}