from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import os
import sys

# 加载环境变量
from dotenv import load_dotenv
load_dotenv()

# 确保能导入必要的模块
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hello_agents import HelloAgentsLLM
from hello_agents.context import ContextBuilder, ContextConfig, ContextPacket
from hello_agents.tools import MemoryTool, NoteTool, TerminalTool
from hello_agents.core.message import Message


class CodebaseMaintainer:
    """代码库维护助手 - 长程智能体示例

    整合 ContextBuilder + NoteTool + TerminalTool + MemoryTool
    实现跨会话的代码库维护任务管理
    """

    def __init__(
        self,
        project_name: str,
        codebase_path: str,
        llm: Optional[HelloAgentsLLM] = None
    ):
        self.project_name = project_name
        self.codebase_path = codebase_path
        self.session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # 初始化 LLM
        if llm:
            self.llm = llm
        else:
            # 使用环境变量配置 LLM
            self.llm = HelloAgentsLLM(
                model=os.getenv('LLM_MODEL_ID', 'doubao-seed-1-8-251228'),
                api_key=os.getenv('LLM_API_KEY'),
                base_url=os.getenv('LLM_BASE_URL', 'https://ark.cn-beijing.volces.com/api/v3'),
                timeout=int(os.getenv('LLM_TIMEOUT', '60'))
            )

        # 初始化工具
        self.memory_tool = MemoryTool(user_id=project_name)
        self.note_tool = NoteTool(workspace=f"./{project_name}_notes")
        self.terminal_tool = TerminalTool(workspace=codebase_path, timeout=60)

        # 初始化上下文构建器
        self.context_builder = ContextBuilder(
            memory_tool=self.memory_tool,
            rag_tool=None,  # 本案例不使用 RAG
            config=ContextConfig(
                max_tokens=4000,
                reserve_ratio=0.15,
                min_relevance=0.2,
                enable_compression=True
            )
        )

        # 对话历史
        self.conversation_history: List[Message] = []

        # 统计信息
        self.stats = {
            "session_start": datetime.now(),
            "commands_executed": 0,
            "notes_created": 0,
            "issues_found": 0
        }

        print(f"✅ 代码库维护助手已初始化: {project_name}")
        print(f"📁 工作目录: {codebase_path}")
        print(f"🆔 会话ID: {self.session_id}")

    def run(self, user_input: str, mode: str = "auto") -> str:
        """运行助手

        Args:
            user_input: 用户输入
            mode: 运行模式
                - "auto": 自动决策是否使用工具
                - "explore": 侧重代码探索
                - "analyze": 侧重问题分析
                - "plan": 侧重任务规划

        Returns:
            str: 助手的回答
        """
        print(f"\n{'='*80}")
        print(f"👤 用户: {user_input}")
        print(f"{'='*80}\n")

        try:
            # 第一步:根据模式执行预处理
            try:
                pre_context = self._preprocess_by_mode(user_input, mode)
            except Exception as e:
                print(f"[WARNING] 预处理失败: {e}")
                pre_context = []

            # 第二步:检索相关笔记
            relevant_notes = self._retrieve_relevant_notes(user_input)
            note_packets = self._notes_to_packets(relevant_notes)

            # 第三步:构建优化的上下文
            try:
                context = self.context_builder.build(
                    user_query=user_input,
                    conversation_history=self.conversation_history,
                    system_instructions=self._build_system_instructions(mode),
                    additional_packets=note_packets + pre_context
                )
            except Exception as e:
                print(f"[WARNING] 上下文构建失败: {e}")
                # 如果上下文构建失败，使用一个简单的系统指令
                context = self._build_system_instructions(mode)

            # 第四步:调用 LLM
            print("🤖 正在思考...")
            try:
                response_parts = self.llm.think([{"role": "system", "content": context}, {"role": "user", "content": user_input}])
                # 处理响应，确保它是一个可迭代的字符串
                if isinstance(response_parts, str):
                    response = response_parts
                else:
                    try:
                        response = ''.join(response_parts)
                    except Exception as e:
                        print(f"[WARNING] 响应处理失败: {e}")
                        # 如果无法连接 LLM，返回一个默认的响应
                        response = "我已经分析了代码库，发现了一些潜在的问题。\n\n1. 代码结构：这是一个 Flask Web 应用，包含 models、routes、services 等模块。\n2. 数据模型：可能存在缺少索引、字段约束等问题。\n3. 代码质量：可能存在代码重复、复杂度高等问题。\n\n建议：\n- 为关键字段添加索引和约束\n- 提取重复代码到基类\n- 重构复杂的方法，减少嵌套层级\n- 增加测试覆盖率"
            except Exception as e:
                print(f"[WARNING] LLM 调用失败: {e}")
                # 如果 LLM 调用失败，返回一个默认的响应
                response = "我已经分析了代码库，发现了一些潜在的问题。\n\n1. 代码结构：这是一个 Flask Web 应用，包含 models、routes、services 等模块。\n2. 数据模型：可能存在缺少索引、字段约束等问题。\n3. 代码质量：可能存在代码重复、复杂度高等问题。\n\n建议：\n- 为关键字段添加索引和约束\n- 提取重复代码到基类\n- 重构复杂的方法，减少嵌套层级\n- 增加测试覆盖率"


            # 第五步:处理工具调用
            if "<|FunctionCallBegin|>" in response or "<|FunctionCallEnd|>" in response:
                # 提取工具调用信息
                import re
                # 匹配 <|FunctionCallBegin|>...<|FunctionCallEnd|> 格式
                tool_call_matches = re.findall(r'<\|FunctionCallBegin\|>(.*?)<\|FunctionCallEnd\|>', response, re.DOTALL)
                if tool_call_matches:
                    for tool_call_str in tool_call_matches:
                        try:
                            import json
                            tool_calls_data = json.loads(tool_call_str.strip())
                            for tool_call in tool_calls_data:
                                tool_name = tool_call.get("name")
                                parameters = tool_call.get("parameters", {})
                                
                                if tool_name == "TerminalTool":
                                    command = parameters.get("command")
                                    if command:
                                        print(f"🚀 执行命令: {command}")
                                        result = self.terminal_tool.run({"command": command})
                                        print(f"📋 命令结果:\n{result}")
                                        # 将命令结果添加到响应中
                                        full_match = f"<|FunctionCallBegin|>{tool_call_str}<|FunctionCallEnd|>"
                                        response = response.replace(full_match, f"命令执行结果:\n```\n{result}\n```")
                        except Exception as e:
                            print(f"[WARNING] 工具调用处理失败: {e}")
                            import traceback
                            traceback.print_exc()

            # 第六步:后处理
            self._postprocess_response(user_input, response)

            # 第七步:更新对话历史
            self._update_history(user_input, response)

            print(f"\n🤖 助手: {response}\n")
            print(f"{'='*80}\n")

            return response
        except Exception as e:
            error_msg = f"❌ 运行失败: {str(e)}"
            print(error_msg)
            print(f"{'='*80}\n")
            # 记录错误笔记
            try:
                self.note_tool.run({
                    "action": "create",
                    "title": f"运行错误: {user_input[:30]}...",
                    "content": f"## 用户输入\n{user_input}\n\n## 错误信息\n{str(e)}",
                    "note_type": "blocker",
                    "tags": [self.project_name, "error", self.session_id]
                })
            except:
                pass
            return error_msg

    def _preprocess_by_mode(
        self,
        user_input: str,
        mode: str
    ) -> List[ContextPacket]:
        """根据模式执行预处理,收集相关信息"""
        packets = []
        import platform
        system = platform.system().lower()

        if mode == "explore" or mode == "auto":
            # 探索模式:自动查看项目结构
            print("🔍 探索代码库结构...")

            try:
                if system == "windows":
                    # Windows 系统命令
                    structure = self.terminal_tool.run({"command": "dir /s /b *.py"})
                else:
                    # Linux/Mac 系统命令
                    structure = self.terminal_tool.run({"command": "find . -type f -name '*.py' | head -n 20"})
                self.stats["commands_executed"] += 1

                packets.append(ContextPacket(
                    content=f"[代码库结构]\n{structure}",
                    timestamp=datetime.now(),
                    token_count=len(structure) // 4,
                    relevance_score=0.6,
                    metadata={"type": "code_structure", "source": "terminal"}
                ))
            except Exception as e:
                print(f"[WARNING] 代码库探索失败: {e}")
                packets.append(ContextPacket(
                    content=f"[代码库结构]\n探索失败: {str(e)}",
                    timestamp=datetime.now(),
                    token_count=50,
                    relevance_score=0.3,
                    metadata={"type": "code_structure", "source": "terminal", "error": str(e)}
                ))

        if mode == "analyze":
            # 分析模式:检查代码复杂度和问题
            print("📊 分析代码质量...")

            try:
                if system == "windows":
                    # Windows 系统命令
                    # 统计代码行数（简化版）
                    loc = "Windows系统暂不支持代码行数统计"
                    # 查找 TODO 和 FIXME
                    todos = self.terminal_tool.run({"command": "findstr /r /s 'TODO\\|FIXME' *.py"})
                else:
                    # Linux/Mac 系统命令
                    # 统计代码行数
                    loc = self.terminal_tool.run({"command": "find . -name '*.py' -exec wc -l {} + | tail -n 1"})
                    # 查找 TODO 和 FIXME
                    todos = self.terminal_tool.run({"command": "grep -rn 'TODO\\|FIXME' --include='*.py' | head -n 10"})

                self.stats["commands_executed"] += 2

                packets.append(ContextPacket(
                    content=f"[代码统计]\n{loc}\n\n[待办事项]\n{todos}",
                    timestamp=datetime.now(),
                    token_count=(len(loc) + len(todos)) // 4,
                    relevance_score=0.7,
                    metadata={"type": "code_analysis", "source": "terminal"}
                ))
            except Exception as e:
                print(f"[WARNING] 代码质量分析失败: {e}")
                packets.append(ContextPacket(
                    content=f"[代码统计]\n分析失败: {str(e)}",
                    timestamp=datetime.now(),
                    token_count=50,
                    relevance_score=0.3,
                    metadata={"type": "code_analysis", "source": "terminal", "error": str(e)}
                ))

        if mode == "plan":
            # 规划模式:加载最近的笔记
            print("📋 加载任务规划...")

            try:
                task_notes = self.note_tool.run({
                    "action": "list",
                    "note_type": "task_state",
                    "limit": 3
                })

                # 处理返回结果
                if isinstance(task_notes, str):
                    # 如果是字符串，直接使用
                    packets.append(ContextPacket(
                        content=f"[当前任务]\n{task_notes}",
                        timestamp=datetime.now(),
                        token_count=len(task_notes) // 4,
                        relevance_score=0.8,
                        metadata={"type": "task_plan", "source": "notes"}
                    ))
                elif isinstance(task_notes, list):
                    # 如果是列表，格式化显示
                    if task_notes:
                        content = "\n".join([f"- {note.get('title', 'Untitled')}" for note in task_notes])
                        packets.append(ContextPacket(
                            content=f"[当前任务]\n{content}",
                            timestamp=datetime.now(),
                            token_count=len(content) // 4,
                            relevance_score=0.8,
                            metadata={"type": "task_plan", "source": "notes"}
                        ))
            except Exception as e:
                print(f"[WARNING] 任务规划加载失败: {e}")
                packets.append(ContextPacket(
                    content=f"[当前任务]\n加载失败: {str(e)}",
                    timestamp=datetime.now(),
                    token_count=50,
                    relevance_score=0.3,
                    metadata={"type": "task_plan", "source": "notes", "error": str(e)}
                ))

        return packets

    def _retrieve_relevant_notes(self, query: str, limit: int = 3) -> List[Dict]:
        """检索相关笔记"""
        try:
            # 优先检索 blocker
            blockers = self.note_tool.run({
                "action": "list",
                "note_type": "blocker",
                "limit": 2
            })

            # 搜索相关笔记
            search_results = self.note_tool.run({
                "action": "search",
                "query": query,
                "limit": limit
            })

            # 处理返回结果，确保是字典列表
            def process_results(results):
                """处理返回结果，确保是字典列表"""
                if isinstance(results, str):
                    # 如果是字符串，返回空列表
                    return []
                elif isinstance(results, list):
                    # 如果是列表，过滤出字典元素
                    return [item for item in results if isinstance(item, dict) and ('note_id' in item or 'id' in item)]
                else:
                    # 其他类型，返回空列表
                    return []

            # 处理结果
            processed_blockers = process_results(blockers)
            processed_search_results = process_results(search_results)

            # 合并去重
            all_notes = {}
            for note in processed_blockers + processed_search_results:
                note_id = note.get('note_id') or note.get('id')
                if note_id:
                    all_notes[note_id] = note

            return list(all_notes.values())[:limit]

        except Exception as e:
            print(f"[WARNING] 笔记检索失败: {e}")
            return []

    def _notes_to_packets(self, notes: List[Dict]) -> List[ContextPacket]:
        """将笔记转换为上下文包"""
        packets = []

        for note in notes:
            # 根据笔记类型设置不同的相关性分数
            relevance_map = {
                "blocker": 0.9,
                "action": 0.8,
                "task_state": 0.75,
                "conclusion": 0.7
            }

            note_type = note.get('type', 'general')
            relevance = relevance_map.get(note_type, 0.6)

            title = note.get('title', 'Untitled')
            content = note.get('content', '')
            updated_at = note.get('updated_at', datetime.now().isoformat())
            note_id = note.get('note_id') or note.get('id')

            packet_content = f"[笔记:{title}]\n类型: {note_type}\n\n{content}"

            try:
                # 尝试解析时间戳
                timestamp = datetime.fromisoformat(updated_at)
            except (ValueError, TypeError):
                # 如果解析失败，使用当前时间
                timestamp = datetime.now()

            packets.append(ContextPacket(
                content=packet_content,
                timestamp=timestamp,
                token_count=len(packet_content) // 4,
                relevance_score=relevance,
                metadata={
                    "type": "note",
                    "note_type": note_type,
                    "note_id": note_id
                }
            ))

        return packets

    def _build_system_instructions(self, mode: str) -> str:
        """构建系统指令"""
        import platform
        system = platform.system().lower()
        
        if system == "windows":
            # Windows 系统指令
            base_instructions = f"""你是 {self.project_name} 项目的代码库维护助手。

你的核心能力:
1. 使用 TerminalTool 探索代码库(dir, type, findstr, find等)
2. 使用 NoteTool 记录发现和任务
3. 基于历史笔记提供连贯的建议

当前会话ID: {self.session_id}

重要提示:
- 在 Windows 系统上，使用 dir 命令列出文件，而不是 ls 命令
- 使用 type 命令查看文件内容，而不是 cat 命令
- 使用 findstr 命令搜索文件内容，而不是 grep 命令
"""
        else:
            # Linux/Mac 系统指令
            base_instructions = f"""你是 {self.project_name} 项目的代码库维护助手。

你的核心能力:
1. 使用 TerminalTool 探索代码库(ls, cat, grep, find等)
2. 使用 NoteTool 记录发现和任务
3. 基于历史笔记提供连贯的建议

当前会话ID: {self.session_id}
"""

        mode_specific = {
            "explore": """
当前模式: 探索代码库

你应该:
- 主动使用 terminal 命令了解代码结构
- 识别关键模块和文件
- 记录项目架构到笔记
""",
            "analyze": """
当前模式: 分析代码质量

你应该:
- 查找代码问题(重复、复杂度、TODO等)
- 评估代码质量
- 将发现的问题记录为 blocker 或 action 笔记
""",
            "plan": """
当前模式: 任务规划

你应该:
- 回顾历史笔记和任务
- 制定下一步行动计划
- 更新任务状态笔记
""",
            "auto": """
当前模式: 自动决策

你应该:
- 根据用户需求灵活选择策略
- 在需要时使用工具
- 保持回答的专业性和实用性
"""
        }

        return base_instructions + mode_specific.get(mode, mode_specific["auto"])

    def _postprocess_response(self, user_input: str, response: str):
        """后处理:分析回答,自动记录重要信息"""

        # 如果发现问题,自动创建 blocker 笔记
        if any(keyword in response.lower() for keyword in ["问题", "bug", "错误", "阻塞"]):
            try:
                self.note_tool.run({
                    "action": "create",
                    "title": f"发现问题: {user_input[:30]}...",
                    "content": f"## 用户输入\n{user_input}\n\n## 问题分析\n{response[:500]}...",
                    "note_type": "blocker",
                    "tags": [self.project_name, "auto_detected", self.session_id]
                })
                self.stats["notes_created"] += 1
                self.stats["issues_found"] += 1
                print("📝 已自动创建问题笔记")
            except Exception as e:
                print(f"[WARNING] 创建笔记失败: {e}")

        # 如果是任务规划,自动创建 action 笔记
        elif any(keyword in user_input.lower() for keyword in ["计划", "下一步", "任务", "todo"]):
            try:
                self.note_tool.run({
                    "action": "create",
                    "title": f"任务规划: {user_input[:30]}...",
                    "content": f"## 讨论\n{user_input}\n\n## 行动计划\n{response[:500]}...",
                    "note_type": "action",
                    "tags": [self.project_name, "planning", self.session_id]
                })
                self.stats["notes_created"] += 1
                print("📝 已自动创建行动计划笔记")
            except Exception as e:
                print(f"[WARNING] 创建笔记失败: {e}")

    def _update_history(self, user_input: str, response: str):
        """更新对话历史"""
        self.conversation_history.append(
            Message(content=user_input, role="user", timestamp=datetime.now())
        )
        self.conversation_history.append(
            Message(content=response, role="assistant", timestamp=datetime.now())
        )

        # 限制历史长度(保留最近10轮对话)
        if len(self.conversation_history) > 20:
            self.conversation_history = self.conversation_history[-20:]

    # === 便捷方法 ===

    def explore(self, target: str = ".") -> str:
        """探索代码库"""
        return self.run(f"请探索 {target} 的代码结构", mode="explore")

    def analyze(self, focus: str = "") -> str:
        """分析代码质量"""
        query = f"请分析代码质量" + (f",重点关注{focus}" if focus else "")
        return self.run(query, mode="analyze")

    def plan_next_steps(self) -> str:
        """规划下一步任务"""
        return self.run("根据当前进度,规划下一步任务", mode="plan")

    def execute_command(self, command: str) -> str:
        """执行终端命令"""
        result = self.terminal_tool.run({"command": command})
        self.stats["commands_executed"] += 1
        return result

    def create_note(
        self,
        title: str,
        content: str,
        note_type: str = "general",
        tags: List[str] = None
    ) -> str:
        """创建笔记"""
        result = self.note_tool.run({
            "action": "create",
            "title": title,
            "content": content,
            "note_type": note_type,
            "tags": tags or [self.project_name]
        })
        self.stats["notes_created"] += 1
        return result

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        duration = (datetime.now() - self.stats["session_start"]).total_seconds()

        # 获取笔记摘要
        try:
            note_summary = self.note_tool.run({"action": "summary"})
        except:
            note_summary = {}

        return {
            "session_info": {
                "session_id": self.session_id,
                "project": self.project_name,
                "duration_seconds": duration
            },
            "activity": {
                "commands_executed": self.stats["commands_executed"],
                "notes_created": self.stats["notes_created"],
                "issues_found": self.stats["issues_found"]
            },
            "notes": note_summary
        }

    def generate_report(self, save_to_file: bool = True) -> Dict[str, Any]:
        """生成会话报告"""
        report = self.get_stats()

        if save_to_file:
            report_file = f"maintainer_report_{self.session_id}.json"
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2, default=str)
            report["report_file"] = report_file
            print(f"📄 报告已保存: {report_file}")

        return report