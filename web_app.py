#!/usr/bin/env python3
"""
代码库维护助手 Web 界面

展示 CodebaseMaintainer 的功能和使用示例
"""

import os
import sys
import json
import time
from datetime import datetime

# 确保能导入必要的模块
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, render_template, request, jsonify
from code_agent.main import CodebaseMaintainer

app = Flask(__name__)
app.secret_key = os.urandom(24)

# 全局变量
maintainer = None  # 维护助手实例
realtime_messages = {}  # 存储实时输出的消息

@app.route('/')
def index():
    """首页"""
    return render_template('index.html', title='代码库维护助手')

@app.route('/about')
def about():
    """关于页面"""
    return render_template('about.html', title='关于代码库维护助手')

@app.route('/analyze-my-flask-app')
def analyze_my_flask_app():
    """分析 my_flask_app 页面"""
    return render_template('analyze_my_flask_app.html', title='分析 my_flask_app')

@app.route('/upload')
def upload():
    """文件上传页面"""
    return render_template('upload.html', title='上传代码文件')

@app.route('/api/init', methods=['POST'])
def api_init():
    """初始化助手"""
    global maintainer
    project_name = request.json.get('project_name', 'my_flask_app')
    codebase_path = request.json.get('codebase_path', './my_flask_app')
    
    try:
        maintainer = CodebaseMaintainer(
            project_name=project_name,
            codebase_path=codebase_path
        )
        return jsonify({'status': 'success', 'message': f'✅ 代码库维护助手已初始化: {project_name}'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'❌ 初始化失败: {str(e)}'})

@app.route('/api/run', methods=['POST'])
def api_run():
    """运行助手"""
    global maintainer
    user_input = request.json.get('user_input', '')
    mode = request.json.get('mode', 'auto')
    
    if not maintainer:
        return jsonify({'status': 'error', 'message': '❌ 助手未初始化'})
    
    try:
        response = maintainer.run(user_input, mode)
        return jsonify({'status': 'success', 'response': response})
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'❌ 运行失败: {str(e)}'})

@app.route('/api/analyze-my-flask-app', methods=['POST'])
def api_analyze_my_flask_app():
    """分析 my_flask_app 代码库"""
    global maintainer
    session_id = request.json.get('session_id', 'default')
    
    try:
        # 初始化会话消息队列
        if session_id not in realtime_messages:
            realtime_messages[session_id] = []
        
        # 添加开始消息
        realtime_messages[session_id].append("🔍 开始分析 my_flask_app 代码库...")
        
        # 初始化维护器（如果尚未初始化）
        if not maintainer:
            realtime_messages[session_id].append("📦 初始化代码库维护助手...")
            maintainer = CodebaseMaintainer(
                project_name='my_flask_app',
                codebase_path='./my_flask_app'
            )
            realtime_messages[session_id].append("✅ 代码库维护助手初始化成功！")
        
        # 执行分析步骤
        results = []
        
        # 第一步：探索代码库
        realtime_messages[session_id].append("🔍 探索代码库结构...")
        try:
            explore_response = maintainer.run('请探索 . 的代码结构，列出所有的 Python 文件和目录结构', mode='explore')
            realtime_messages[session_id].append(f"✅ 探索完成：{explore_response}")
            results.append({
                'step': '探索代码库',
                'response': explore_response
            })
        except Exception as e:
            error_msg = f'探索失败: {str(e)}'
            realtime_messages[session_id].append(f"❌ {error_msg}")
            results.append({
                'step': '探索代码库',
                'response': error_msg
            })
        
        # 第二步：分析代码质量
        realtime_messages[session_id].append("📊 分析代码质量...")
        try:
            analyze_response = maintainer.run('请分析代码库的质量，查找潜在的问题，包括代码重复、复杂度、缺少测试等', mode='analyze')
            realtime_messages[session_id].append(f"✅ 质量分析完成：{analyze_response}")
            results.append({
                'step': '分析代码质量',
                'response': analyze_response
            })
        except Exception as e:
            error_msg = f'分析失败: {str(e)}'
            realtime_messages[session_id].append(f"❌ {error_msg}")
            results.append({
                'step': '分析代码质量',
                'response': error_msg
            })
        
        # 第三步：规划重构任务
        realtime_messages[session_id].append("📋 规划重构任务...")
        try:
            plan_response = maintainer.run('请基于之前的分析，规划重构任务，列出优先级和工作量', mode='plan')
            realtime_messages[session_id].append(f"✅ 任务规划完成：{plan_response}")
            results.append({
                'step': '规划重构任务',
                'response': plan_response
            })
        except Exception as e:
            error_msg = f'规划失败: {str(e)}'
            realtime_messages[session_id].append(f"❌ {error_msg}")
            results.append({
                'step': '规划重构任务',
                'response': error_msg
            })
        
        realtime_messages[session_id].append("🎉 分析完成！")
        
        return jsonify({'status': 'success', 'results': results})
    except Exception as e:
        error_msg = f'❌ 分析失败: {str(e)}'
        if session_id in realtime_messages:
            realtime_messages[session_id].append(error_msg)
        return jsonify({'status': 'error', 'message': error_msg})



@app.route('/api/upload', methods=['POST'])
def api_upload():
    """上传代码文件并分析"""
    if 'file' not in request.files:
        return jsonify({'status': 'error', 'message': '❌ 未收到文件'})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'status': 'error', 'message': '❌ 文件名不能为空'})
    
    # 创建 tem 目录 - 使用正确的路径
    code_agent_dir = os.path.dirname(__file__)
    tem_dir = os.path.join(code_agent_dir, 'my_flask_app', 'tem')
    os.makedirs(tem_dir, exist_ok=True)
    
    # 保存文件
    file_path = os.path.join(tem_dir, file.filename)
    file.save(file_path)
    
    print(f"✅ 文件已保存到: {file_path}")
    
    # 分析文件
    try:
        # 初始化临时维护器
        temp_maintainer = CodebaseMaintainer(
            project_name='temp_project',
            codebase_path=tem_dir
        )
        
        # 读取文件内容
        with open(file_path, 'r', encoding='utf-8') as f:
            file_content = f.read()
        
        # 分析上传的文件
        response = temp_maintainer.run(f'请分析以下代码文件的质量和潜在问题：\n\n文件名: {file.filename}\n\n代码内容:\n```python\n{file_content}\n```')
        return jsonify({'status': 'success', 'response': response, 'filename': file.filename, 'filepath': file_path})
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'❌ 分析失败: {str(e)}'})

@app.route('/api/stream/<session_id>')
def api_stream(session_id):
    """服务器发送事件 (SSE) 端点，用于实时输出内容"""
    def event_stream():
        # 初始化会话消息
        if session_id not in realtime_messages:
            realtime_messages[session_id] = []
        
        # 发送初始消息
        yield 'data: {"type": "info", "message": "开始分析..."}\n\n'
        
        # 持续发送消息
        last_index = 0
        while True:
            messages = realtime_messages.get(session_id, [])
            if len(messages) > last_index:
                for msg in messages[last_index:]:
                    yield 'data: ' + json.dumps({"type": "message", "message": msg}, ensure_ascii=False) + '\n\n'
                last_index = len(messages)
            time.sleep(0.5)
    
    return app.response_class(event_stream(), mimetype='text/event-stream')

@app.route('/api/clear-stream/<session_id>', methods=['POST'])
def api_clear_stream(session_id):
    """清除指定会话的消息"""
    if session_id in realtime_messages:
        del realtime_messages[session_id]
    return jsonify({'status': 'success'})


if __name__ == '__main__':
    # 创建 templates 目录
    templates_dir = os.path.join(os.path.dirname(__file__), 'templates')
    os.makedirs(templates_dir, exist_ok=True)
    
    # 创建基础模板文件
    base_template = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }} - 代码库维护助手</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {
            background-color: #f8f9fa;
        }
        .navbar {
            background-color: #343a40;
        }
        .navbar-brand {
            color: #ffffff;
        }
        .navbar-nav .nav-link {
            color: rgba(255, 255, 255, 0.8);
        }
        .navbar-nav .nav-link:hover {
            color: #ffffff;
        }
        .container {
            margin-top: 20px;
            margin-bottom: 40px;
        }
        .card {
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        .code-block {
            background-color: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 4px;
            padding: 15px;
            font-family: 'Courier New', Courier, monospace;
            white-space: pre-wrap;
            margin-top: 10px;
            margin-bottom: 10px;
        }
        .result-block {
            background-color: #e9ecef;
            border: 1px solid #dee2e6;
            border-radius: 4px;
            padding: 15px;
            margin-top: 10px;
            margin-bottom: 10px;
        }
        .step-card {
            margin-bottom: 20px;
        }
        .step-title {
            font-weight: bold;
            margin-bottom: 10px;
        }
        .step-description {
            color: #6c757d;
            margin-bottom: 15px;
        }
        .btn-primary {
            background-color: #0d6efd;
            border-color: #0d6efd;
        }
        .btn-success {
            background-color: #198754;
            border-color: #198754;
        }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg">
        <div class="container-fluid">
            <a class="navbar-brand" href="/">代码库维护助手</a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav">
                    <li class="nav-item">
                        <a class="nav-link" href="/">首页</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="/analyze-my-flask-app">分析 my_flask_app</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="/upload">上传代码文件</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="/about">关于</a>
                    </li>
                </ul>
            </div>
        </div>
    </nav>
    
    <div class="container">
        <h1 class="mt-4 mb-4">{{ title }}</h1>
        {% block content %}{% endblock %}
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    {% block scripts %}{% endblock %}
</body>
</html>'''
    
    # 创建首页模板
    index_template = '''{% extends "base.html" %}
{% block content %}
    <div class="card">
        <div class="card-body">
            <h2 class="card-title">代码库维护助手</h2>
            <p class="card-text">一个智能的代码库维护工具，帮助您探索代码结构、分析代码质量、规划重构任务。</p>
            
            <h3 class="mt-4">核心功能</h3>
            <div class="row mt-3">
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-body">
                            <h5 class="card-title">📦 分析 my_flask_app</h5>
                            <p class="card-text">自动分析 my_flask_app 目录下的代码库，包括代码结构探索、质量分析和任务规划。</p>
                            <a href="/analyze-my-flask-app" class="btn btn-primary">开始分析</a>
                        </div>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-body">
                            <h5 class="card-title">📤 上传代码文件</h5>
                            <p class="card-text">上传单个代码文件进行分析，支持 Python 等常见编程语言的质量分析。</p>
                            <a href="/upload" class="btn btn-success">上传文件</a>
                        </div>
                    </div>
                </div>
            </div>
            
            <h3 class="mt-4">关于 use.py</h3>
            <div class="card mt-3">
                <div class="card-body">
                    <p><code>use.py</code> 是一个使用示例，展示了如何使用 <code>CodebaseMaintainer</code> 类来维护代码库。</p>
                    <p>本 Web 应用基于相同的 <code>CodebaseMaintainer</code> 类，提供了可视化的界面来执行相同的功能。</p>
                </div>
            </div>
        </div>
    </div>
{% endblock %}'''
    
    # 创建关于页面模板
    about_template = '''{% extends "base.html" %}
{% block content %}
    <div class="card">
        <div class="card-body">
            <h2 class="card-title">关于代码库维护助手</h2>
            <p class="card-text">代码库维护助手是一个智能的工具，帮助开发者更有效地管理和维护代码库。</p>
            
            <h3 class="mt-4">技术特点</h3>
            <ul class="list-group list-group-flush mt-2">
                <li class="list-group-item">
                    <strong>长程任务支持</strong>
                    <p class="mt-1">通过 NoteTool 实现跨会话的状态管理，适合持续数天的重构任务。</p>
                </li>
                <li class="list-group-item">
                    <strong>智能上下文</strong>
                    <p class="mt-1">通过 ContextBuilder 构建优化的上下文，确保高信号密度，避免信息过载。</p>
                </li>
                <li class="list-group-item">
                    <strong>按需探索</strong>
                    <p class="mt-1">通过 TerminalTool 实现即时、按需的代码探索，只在需要时查看具体文件。</p>
                </li>
            </ul>
            
            <h3 class="mt-4">文件说明</h3>
            <ul class="mt-2">
                <li><strong>main.py</strong>: 包含 CodebaseMaintainer 类，是核心功能实现</li>
                <li><strong>use.py</strong>: 使用示例，展示如何在命令行中使用 CodebaseMaintainer</li>
                <li><strong>web_app.py</strong>: Web 应用，提供可视化界面</li>
                <li><strong>my_flask_app/</strong>: 示例代码库，用于演示分析功能</li>
            </ul>
        </div>
    </div>
{% endblock %}'''
    
    # 创建分析 my_flask_app 页面模板
    analyze_my_flask_app_template = '''{% extends "base.html" %}
{% block content %}
    <div class="card">
        <div class="card-body">
            <h2 class="card-title">分析 my_flask_app</h2>
            <p class="card-text">自动分析 my_flask_app 目录下的代码库，包括代码结构探索、质量分析和任务规划。</p>
            
            <button id="analyze-btn" class="btn btn-primary btn-lg">开始分析 my_flask_app</button>
            <button id="clear-btn" class="btn btn-secondary btn-lg ml-2">清除输出</button>
            
           <div id="realtime-output" class="mt-4 p-3 bg-light rounded border" style="white-space: pre-wrap; word-wrap: break-word; overflow: visible; height: auto;">
    <h4>实时输出</h4>
    <div id="output-content" class="mt-2">
        <p>点击上方按钮开始分析...</p>
    </div>
</div>
            
            <div id="results" class="mt-4 d-none">
                <h3>分析结果</h3>
                <div id="results-content"></div>
            </div>
        </div>
    </div>
{% endblock %}

{% block scripts %}
    <script>
        let sessionId = 'session_' + Date.now();
        let eventSource = null;
        
        // 清除输出
        document.getElementById('clear-btn').addEventListener('click', function() {
            document.getElementById('output-content').innerHTML = '<p>点击上方按钮开始分析...</p>';
            fetch(`/api/clear-stream/${sessionId}`, {
                method: 'POST'
            });
        });
        
        // 开始分析
        document.getElementById('analyze-btn').addEventListener('click', function() {
            const btn = this;
            const resultsDiv = document.getElementById('results');
            const resultsContent = document.getElementById('results-content');
            const outputContent = document.getElementById('output-content');
            
            // 生成新的会话ID
            sessionId = 'session_' + Date.now();
            
            // 清除之前的输出
            outputContent.innerHTML = '<p>开始分析...</p>';
            
            // 启动SSE连接
            if (eventSource) {
                eventSource.close();
            }
            eventSource = new EventSource(`/api/stream/${sessionId}`);
            
            eventSource.onmessage = function(event) {
                try {
                    const data = JSON.parse(event.data);
                    if (data.type === 'message' || data.type === 'info') {
                        const p = document.createElement('p');
                        p.textContent = data.message;
                        outputContent.appendChild(p);
                        // 滚动到底部
                        outputContent.scrollTop = outputContent.scrollHeight;
                    }
                } catch (e) {
                    console.error('Error parsing SSE message:', e);
                }
            };
            
            eventSource.onerror = function() {
                eventSource.close();
            };
            
            btn.disabled = true;
            btn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> 分析中...';
            resultsDiv.classList.remove('d-none');
            resultsContent.innerHTML = '<div class="text-center"><div class="spinner-border" role="status"><span class="sr-only">分析中...</span></div><p class="mt-2">正在分析代码库，请稍候...</p></div>';
            
            fetch('/api/analyze-my-flask-app', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ session_id: sessionId })
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    let html = '';
                    data.results.forEach(result => {
                        html += `
                            <div class="card step-card">
                                <div class="card-header">
                                    <h4>${result.step}</h4>
                                </div>
                                <div class="card-body">
                                    <div class="result-block">
                                        ${result.response.replace(/\\n/g, '<br>')}
                                    </div>
                                </div>
                            </div>
                        `;
                    });
                    resultsContent.innerHTML = html;
                } else {
                    resultsContent.innerHTML = `<div class="alert alert-danger">${data.message}</div>`;
                }
                btn.disabled = false;
                btn.innerHTML = '重新分析';
                // 关闭SSE连接
                if (eventSource) {
                    eventSource.close();
                }
            })
            .catch(error => {
                resultsContent.innerHTML = `<div class="alert alert-danger">❌ 分析失败: ${error.message}</div>`;
                btn.disabled = false;
                btn.innerHTML = '重新分析';
                // 关闭SSE连接
                if (eventSource) {
                    eventSource.close();
                }
            });
        });
    </script>
{% endblock %}''' 
    
    # 创建上传页面模板
    upload_template = '''{% extends "base.html" %}
{% block content %}
    <div class="card">
        <div class="card-body">
            <h2 class="card-title">上传代码文件</h2>
            <p class="card-text">上传单个代码文件进行分析，支持 Python 等常见编程语言。</p>
            
            <form id="upload-form" enctype="multipart/form-data">
                <div class="mb-3">
                    <label for="file" class="form-label">选择文件</label>
                    <input type="file" class="form-control" id="file" name="file" required>
                </div>
                <button type="submit" class="btn btn-primary">上传并分析</button>
            </form>
            
            <div id="realtime-output" class="mt-4 p-3 bg-light rounded border" style="white-space: pre-wrap; word-wrap: break-word; overflow: visible; height: auto;">
    <h4>实时输出</h4>
    <div id="output-content" class="mt-2">
        <p>选择文件并点击上传按钮开始分析...</p>
    </div>
</div>
            
            <div id="result" class="mt-4 d-none">
                <div class="card">
                    <div class="card-header">
                        <h4>分析结果</h4>
                    </div>
                    <div class="card-body">
                        <div id="result-content"></div>
                    </div>
                </div>
            </div>
        </div>
    </div>
{% endblock %}

{% block scripts %}
    <script>
        document.getElementById('upload-form').addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const resultDiv = document.getElementById('result');
            const resultContent = document.getElementById('result-content');
            const outputContent = document.getElementById('output-content');
            
            // 显示实时输出
            outputContent.innerHTML = '<p>正在上传文件...</p>';
            
            resultContent.innerHTML = '<div class="text-center"><div class="spinner-border" role="status"><span class="sr-only">分析中...</span></div><p class="mt-2">正在分析代码，请稍候...</p></div>';
            resultDiv.classList.remove('d-none');
            
            fetch('/api/upload', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    outputContent.innerHTML += '<p>✅ 文件上传成功！</p>';
                    outputContent.innerHTML += '<p>📊 分析完成！</p>';
                    resultContent.innerHTML = `
                        <p class="text-success">✅ 文件 <strong>${data.filename}</strong> 已成功上传并分析</p>
                        <div class="result-block">
                            ${data.response.replace(/\\n/g, '<br>')}
                        </div>
                    `;
                } else {
                    outputContent.innerHTML += `<p class="text-danger">❌ ${data.message}</p>`;
                    resultContent.innerHTML = `<div class="alert alert-danger">${data.message}</div>`;
                }
            })
            .catch(error => {
                outputContent.innerHTML += `<p class="text-danger">❌ 上传失败: ${error.message}</p>`;
                resultContent.innerHTML = `<div class="alert alert-danger">❌ 上传失败: ${error.message}</div>`;
            });
        });
    </script>
{% endblock %}''' 
    
    # 写入模板文件
    with open(os.path.join(templates_dir, 'base.html'), 'w', encoding='utf-8') as f:
        f.write(base_template)
    
    with open(os.path.join(templates_dir, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(index_template)
    
    with open(os.path.join(templates_dir, 'about.html'), 'w', encoding='utf-8') as f:
        f.write(about_template)
    
    with open(os.path.join(templates_dir, 'analyze_my_flask_app.html'), 'w', encoding='utf-8') as f:
        f.write(analyze_my_flask_app_template)
    
    with open(os.path.join(templates_dir, 'upload.html'), 'w', encoding='utf-8') as f:
        f.write(upload_template)
    
    print("✅ Web 应用已创建成功！")
    print("📁 生成的文件：")
    print("   - code_agent/web_app.py       # Web 应用主文件")
    print("   - code_agent/templates/        # 模板目录")
    print("   - code_agent/templates/base.html      # 基础模板")
    print("   - code_agent/templates/index.html     # 首页模板")
    print("   - code_agent/templates/about.html     # 关于页面模板")
    print("   - code_agent/templates/analyze_my_flask_app.html # 分析 my_flask_app 页面")
    print("   - code_agent/templates/upload.html    # 上传页面模板")
    print("\\n🚀 启动 Web 应用：")
    print("   cd code_agent")
    print("   python web_app.py")
    print("\\n🌐 访问 Web 应用：")
    print("   http://localhost:5000")
    
    # 启动应用 - 禁用 debug 模式，避免文件变化导致服务重启
    # 或者使用 extra_files 参数来指定要监视的文件
    app.run(debug=False, host='0.0.0.0', port=5000)
