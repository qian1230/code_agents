# Code Agent - 代码库维护助手 Web 界面

这是一个基于 `hello_agents` 框架构建的代码库维护智能体 Web 应用。它提供了一个可视化的界面，利用 LLM (大语言模型) 来帮助开发者探索、分析和维护代码库。

## 📖 项目简介

`code_agent` 是一个演示性质的智能体应用，旨在展示如何利用长程智能体（Long-context Agents）技术来辅助软件工程任务。通过集成 `hello_agents` 框架的记忆（Memory）、工具（Tools）和上下文管理（Context Builder）能力，它能够理解复杂的代码结构并给出专业的维护建议。

## ✨ 功能特性

- **可视化交互**: 基于 Flask 构建的 Web 界面，操作直观便捷。
- **智能分析**: 集成 `CodebaseMaintainer` 智能体，支持对代码库进行深度分析。
- **一键诊断**: 针对内置示例项目 `my_flask_app` 提供一键分析流程，包含：
    - 🔍 **代码探索**: 自动梳理文件结构和依赖关系。
    - 📊 **质量分析**: 识别代码异味、潜在 Bug 和设计缺陷。
    - 📋 **重构规划**: 生成具体的重构任务和优先级建议。
- **实时反馈**: 分析过程通过流式日志实时展示，让用户清晰看到智能体的思考路径和工具调用（如终端命令执行）。
- **文件上传**: 支持上传单个代码文件进行快速分析与解读。

## 🛠️ 环境要求

- Python 3.8+
- 依赖库: 见 `requirements.txt`
- LLM API 密钥 (支持兼容 OpenAI 格式的 API，如火山引擎豆包、DeepSeek 等)

## 🚀 快速开始

### 1. 安装依赖

确保你位于 `code_agent` 目录下：

```bash
pip install -r requirements.txt
```

> **注意**: 本项目依赖上级目录的 `hello_agents` 包。程序运行时会自动将上级目录加入 `PYTHONPATH`，无需手动安装 `hello_agents`。

### 2. 配置环境变量

在项目根目录 `hello_llm` 或本目录 `code_agent` 下创建 `.env` 文件，配置 LLM 相关的环境变量：

```ini
LLM_MODEL_ID=your_model_id          # 例如: doubao-pro-32k
LLM_API_KEY=your_api_key            # 你的 API Key
LLM_BASE_URL=your_api_base_url      # 例如: https://ark.cn-beijing.volces.com/api/v3
LLM_TIMEOUT=60
```

### 3. 运行应用

```bash
python web_app.py
```

启动成功后，控制台将输出服务地址。请在浏览器中访问：

➡️ **http://127.0.0.1:5000**

## 📂 项目结构

```text
code_agent/
├── web_app.py              # Flask Web 应用入口文件
├── main.py                 # CodebaseMaintainer 智能体核心逻辑实现
├── requirements.txt        # Python 依赖列表
├── templates/              # Web 前端 HTML 模板
│   ├── index.html          # 首页
│   ├── analyze.html        # 分析页面
│   └── ...
├── my_flask_app/           # 内置的示例 Flask 项目 (被分析对象代码库)
├── my_flask_app_notes/     # (自动生成) 智能体分析过程中产生的笔记
├── memory_data/            # (自动生成) 智能体记忆存储
└── ...
```

## 🧩 核心组件说明

- **CodebaseMaintainer (`main.py`)**: 
    - 继承自 `hello_agents` 的智能体实现。
    - 整合了 `ContextBuilder` (上下文构建)、`NoteTool` (笔记工具)、`TerminalTool` (终端工具) 和 `MemoryTool` (记忆工具)。
    - 能够跨会话维护对项目的理解。

- **Web Interface (`web_app.py`)**:
    - 提供 RESTful API 和前端页面。
    - 管理智能体实例和会话状态。
    - 处理实时消息推送。

## 📝 使用说明

1. **首页**: 打开浏览器访问 `http://127.0.0.1:5000`。
2. **分析演示**: 点击导航栏或首页的 "分析 my_flask_app" 按钮。
3. **执行分析**: 点击 "开始分析" 按钮，观察右侧的实时日志窗口，智能体将逐步执行任务。
4. **查看报告**: 分析完成后，页面将展示结构化的分析结果和建议。

---
Powered by [hello_llm](..)
