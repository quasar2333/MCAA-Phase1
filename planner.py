# planner.py
import json
from llm_interface import ask_llm
from memory_manager import load_tools

# 这是我们给LLM定义的角色和指令，非常重要！
PLANNER_SYSTEM_PROMPT = """
你是一个AI Agent的规划模块。你的任务是将用户提出的高层级目标分解成一个由多个步骤组成的、清晰的JSON计划。
每个步骤都是一个字典，包含'step_number', 'task', 和 'details'。
'task' 字段必须是以下两种类型之一：
1. "CREATE_NEW_TOOL": 当没有现有工具可以完成这个步骤时使用。
2. "USE_EXISTING_TOOL": 当一个现有工具可以满足需求时使用。

在规划时，你必须首先参考我提供给你的【现有工具列表】。
- 如果有合适的工具，你的计划步骤就应该是 USE_EXISTING_TOOL，并在 'details' 中提供工具的名称。
- 如果没有合适的工具，你就需要创建一个 CREATE_NEW_TOOL 步骤，并在 'details' 中用自然语言清晰地描述需要编写的Python脚本的功能。

你的输出必须是且只能是一个JSON数组，不包含任何解释性文字。

示例输出格式:
[
  {
    "step_number": 1,
    "task": "CREATE_NEW_TOOL",
    "details": "编写一个Python脚本，用于扫描桌面，并列出所有的.txt和.md文件。"
  },
  {
    "step_number": 2,
    "task": "CREATE_NEW_TOOL",
    "details": "编写一个Python脚本，在桌面上创建一个名为'文档备份'的文件夹，如果文件夹已存在则忽略。"
  }
]
"""

def create_plan(goal: str):
    """根据用户目标创建计划。"""
    # 加载现有工具，并格式化后提供给LLM作为上下文
    existing_tools = load_tools()
    if not existing_tools:
        tools_context = "【现有工具列表】:\n无"
    else:
        formatted_tools = "\n".join([f"- {tool['name']}: {tool['description']}" for tool in existing_tools])
        tools_context = f"【现有工具列表】:\n{formatted_tools}"

    # 构造给LLM的最终用户提示
    user_prompt = f"{tools_context}\n\n【用户目标】:\n{goal}"

    print("正在请求LLM进行规划...")
    plan_str = ask_llm(PLANNER_SYSTEM_PROMPT, user_prompt)

    if not plan_str:
        return None

    try:
        # 解析LLM返回的JSON计划
        plan = json.loads(plan_str)
        return plan
    except json.JSONDecodeError:
        print("规划失败：LLM返回的不是有效的JSON格式。")
        print("LLM返回内容:", plan_str)
        return None
