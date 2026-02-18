class OrderService:
    def process_order(self, order_id):
        # 模拟订单处理
        order = {'id': order_id, 'status': 'pending'}
        if order:
            if order['status'] == 'pending':
                product = {'id': 1, 'stock': 10}
                if product:
                    if product['stock'] >= 1:
                        # 处理订单逻辑
                        order['status'] = 'processing'
                        product['stock'] -= 1
                        return True
        return False
