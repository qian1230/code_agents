# react_agent.py
import re
from typing import Optional
from llm_client import HelloAgentsLLM
from tools import ToolExecutor

# ====================== ReAct提示词模板 ======================
REACT_PROMPT_TEMPLATE = """
你是一个可以调用外部工具的智能助手，需严格遵循以下规则：

【可用工具】
{tools}

【输出格式】
Thought: 你的思考过程（分析问题、判断是否需要调用工具、选哪个工具）
Action: 执行的动作（格式：工具名[输入内容] 或 Finish[最终答案]）

【注意】
1. 只有收集到足够信息时，才能用Finish[最终答案]输出结果
2. 工具调用必须严格匹配格式，输入内容需清晰、简洁
3. 优先使用工具获取最新/未知信息，而非凭记忆回答
4. 对于涉及上传文档内容的问题，特别是关于唇读、深度学习、论文等相关问题，应首先使用RAGSearch工具进行检索
5. 只有当RAGSearch工具返回"私有知识库中未找到相关内容"时，才考虑使用其他搜索工具

【当前任务】
Question: {question}
History: {history}
"""

# ====================== ReAct智能体 ======================
class ReActAgent:
    """
    ReAct智能体：整合LLM+工具执行器，实现「思考-行动-观察」闭环
    """
    def __init__(self, llm_client: HelloAgentsLLM, tool_executor: ToolExecutor, max_steps: int = 5):
        self.llm = llm_client          # LLM客户端
        self.tool_executor = tool_executor  # 工具执行器
        self.max_steps = max_steps     # 最大思考步数（防止无限循环）
        self.history = []              # 交互历史

    def _parse_llm_output(self, text: str) -> (Optional[str], Optional[str]):
        """
        解析LLM输出，提取Thought和Action
        :param text: LLM返回的原始文本
        :return: (thought, action) 或 (None, None)
        """
        # 正则匹配Thought（非贪婪匹配，直到Action或文本结束）
        thought_match = re.search(r"Thought:\s*(.*?)(?=\nAction:|$)", text, re.DOTALL)
        # 正则匹配Action（匹配到文本末尾）
        action_match = re.search(r"Action:\s*(.*?)$", text, re.DOTALL)

        thought = thought_match.group(1).strip() if thought_match else None
        action = action_match.group(1).strip() if action_match else None
        return thought, action

    def _parse_action(self, action_text: str) -> (Optional[str], Optional[str]):
        """
        解析Action，提取工具名和输入
        :param action_text: 如 "Search[英伟达最新GPU]"
        :return: (tool_name, tool_input) 或 (None, None)
        """
        match = re.match(r"(\w+)\[(.*)\]", action_text, re.DOTALL)
        if match:
            return match.group(1).strip(), match.group(2).strip()
        return None, None

    def run(self, question: str) -> Optional[str]:
        """
        运行ReAct智能体回答问题
        :param question: 用户问题
        :return: 最终答案（或None）
        """
        self.history = []  # 重置历史
        current_step = 0

        while current_step < self.max_steps:
            current_step += 1
            print(f"\n========== 第 {current_step} 步 ==========")

            # 1. 构建提示词
            tools_desc = self.tool_executor.getAvailableTools()
            history_str = "\n".join(self.history)
            prompt = REACT_PROMPT_TEMPLATE.format(
                tools=tools_desc,
                question=question,
                history=history_str
            )

            # 2. 调用LLM思考
            messages = [{"role": "user", "content": prompt}]
            llm_response = self.llm.think(messages, temperature=0.5)
            if not llm_response:
                print("❌ LLM无有效响应，终止流程")
                break

            # 3. 解析LLM输出
            thought, action = self._parse_llm_output(llm_response)
            if not thought or not action:
                print("❌ 解析失败：未找到Thought/Action，终止流程")
                break
            print(f"\n🤔 思考：{thought}")

            # 4. 处理Action
            # 4.1 结束流程（Finish）
            if action.startswith("Finish"):
                finish_match = re.match(r"Finish\[(.*)\]", action, re.DOTALL)
                final_answer = finish_match.group(1).strip() if finish_match else "无有效答案"
                print(f"\n🎉 最终答案：{final_answer}")
                return final_answer

            # 4.2 调用工具
            tool_name, tool_input = self._parse_action(action)
            if not tool_name or not tool_input:
                observation = f"错误：Action格式无效 → {action}（正确格式：工具名[输入内容]）"
            else:
                print(f"\n🎬 行动：{tool_name}[{tool_input}]")
                # 执行工具
                tool_func = self.tool_executor.getTool(tool_name)
                if not tool_func:
                    observation = f"错误：未找到工具[{tool_name}]"
                else:
                    observation = tool_func(tool_input)

            # 5. 记录观察结果，更新历史
            print(f"\n👀 观察：{observation}")
            self.history.extend([
                f"Thought: {thought}",
                f"Action: {action}",
                f"Observation: {observation}"
            ])

        # 达到最大步数
        print(f"\n⏹️ 已达到最大步数（{self.max_steps}步），终止流程")
        return None

# ====================== 运行示例 ======================
if __name__ == '__main__':
    try:
        # 1. 初始化LLM客户端
        llm = HelloAgentsLLM()

        # 2. 初始化工具执行器+注册搜索工具
        tool_exec = ToolExecutor()
        tool_exec.registerTool(
            name="Search",
            description="网页搜索引擎：用于获取时事、最新数据、事实性信息，输入为搜索关键词",
            func=lambda q: __import__('tools').search(q)  # 避免循环导入
        )

        # 3. 初始化ReAct智能体
        agent = ReActAgent(
            llm_client=llm,
            tool_executor=tool_exec,
            max_steps=5
        )

        # 4. 运行智能体
        user_question = "2025年英伟达最新发布的GPU型号是什么？"
        print(f"📌 用户问题：{user_question}")
        agent.run(user_question)

    except Exception as e:
        print(f"❌ 运行失败：{str(e)}")