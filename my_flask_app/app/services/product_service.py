class ProductService:
    def get_product(self, product_id):
        # 模拟获取产品
        return {'id': product_id, 'name': 'Product'}
    
    def create_product(self, product_data):
        # 模拟创建产品
        return {'id': 1, **product_data}
    
    def update_product(self, product_id, product_data):
        # 模拟更新产品
        return {'id': product_id, **product_data}
    
    def delete_product(self, product_id):
        # 模拟删除产品
        return True
