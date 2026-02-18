class Order:
    def __init__(self, id, user_id, product_id, quantity, status):
        self.id = id
        self.user_id = user_id
        self.product_id = product_id
        self.quantity = quantity
        self.status = status
        
    def __repr__(self):
        return f"<Order {self.id}>"
