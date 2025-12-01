class Pizza:

    def __init__(self, name: str, size: str, compositon: str, production_time: int, price: str):
        self.name = name
        self.size = size
        self.composition = compositon
        self.production_time = int(production_time)
        self.price = price

    def __str__(self):
        return ("\n+-------------------------------------------------+\n"
                 f"| Nom             | {self.name:29} |\n"
                 f"| Taille          | {self.size:29} |\n"
                 f"| Composition     | {self.composition} |\n"
                 f"| TPsProd         | {str(self.production_time):29} |\n"
                 f"| Prix            | {str(self.price):29} |\n"
                 f"+-------------------------------------------------+\n")
        

    def print_pizza(self):
        display = ""
        for ingredient in self.composition:
            if ingredient == "R":
                display += "🟥"
            elif ingredient == "J":
                display += "🟨"
            elif ingredient == "V":
                display += "🟩"
            elif ingredient == "B":
                display += "🟦"
            elif ingredient == "-":
                display += "⬛"
            else:
                display += "\n"
        print(display)
        return display
