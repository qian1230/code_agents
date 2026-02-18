#!/usr/bin/env python3
"""
为 my_flask_app 添加基本的代码
"""

import os
import sys

def create_file(file_path, content):
    """创建文件"""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✅ 已创建: {file_path}")

def main():
    base_dir = os.path.join(os.path.dirname(__file__), 'my_flask_app')
    
    # 1. 创建基本的 __init__.py 文件
    init_content = '''"""Python 包初始化文件"""
'''
    create_file(os.path.join(base_dir, '__init__.py'), init_content)
    create_file(os.path.join(base_dir, 'app', '__init__.py'), init_content)
    create_file(os.path.join(base_dir, 'app', 'models', '__init__.py'), init_content)
    create_file(os.path.join(base_dir, 'app', 'routes', '__init__.py'), init_content)
    create_file(os.path.join(base_dir, 'app', 'services', '__init__.py'), init_content)
    
    # 2. 创建基本的配置文件
    config_content = '''"""应用配置"""
import os

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    DEBUG = True
'''
    create_file(os.path.join(base_dir, 'config.py'), config_content)
    
    # 3. 创建一个简单的模型文件
    user_model_content = '''"""用户模型"""

class User:
    def __init__(self, id, username, email):
        self.id = id
        self.username = username
        self.email = email
'''
    create_file(os.path.join(base_dir, 'app', 'models', 'user.py'), user_model_content)
    
    # 4. 创建一个简单的路由文件
    user_routes_content = '''"""用户路由"""
from flask import Blueprint

user_bp = Blueprint('user', __name__)

@user_bp.route('/users')
def get_users():
    return 'Users List'
'''
    create_file(os.path.join(base_dir, 'app', 'routes', 'user_routes.py'), user_routes_content)
    
    # 5. 创建一个简单的服务文件
    user_service_content = '''"""用户服务"""

class UserService:
    def get_users(self):
        return []
'''
    create_file(os.path.join(base_dir, 'app', 'services', 'user_service.py'), user_service_content)
    
    # 6. 创建一个简单的启动文件
    run_content = '''#!/usr/bin/env python3
"""启动应用"""
print('Hello, Flask!')
'''
    create_file(os.path.join(base_dir, 'run.py'), run_content)
    
    print("\n" + "="*80)
    print("✅ 基本文件创建完成！")
    print("="*80)
    print("\n📁 创建的文件结构：")
    print("  my_flask_app/")
    print("  ├── __init__.py")
    print("  ├── config.py")
    print("  ├── run.py")
    print("  └── app/")
    print("      ├── __init__.py")
    print("      ├── models/")
    print("      │   ├── __init__.py")
    print("      │   └── user.py")
    print("      ├── routes/")
    print("      │   ├── __init__.py")
    print("      │   └── user_routes.py")
    print("      └── services/")
    print("          ├── __init__.py")
    print("          └── user_service.py")
    print("\n🚀 现在可以运行 use.py 或 web_app.py 来分析这些代码了！")

if __name__ == '__main__':
    main()
