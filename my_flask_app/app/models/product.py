class Product:
    def __init__(self, id, name, description, price, stock):
        self.id = id
        self.name = name
        self.description = description
        self.price = price
        self.stock = stock
        
    def __repr__(self):
        return f"<Product {self.name}>"
