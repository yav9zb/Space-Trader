class Commodity:
    def __init__(self, name, base_price):
        self.name = name
        self.base_price = base_price
        self.quantity = 0

class Market:
    def __init__(self):
        self.commodities = {
            'Iron': Commodity('Iron', 100),
            'Gold': Commodity('Gold', 500),
            'Food': Commodity('Food', 50)
        }