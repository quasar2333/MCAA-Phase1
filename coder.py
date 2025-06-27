# coder.py
from llm_interface import ask_llm

CODER_SYSTEM_PROMPT = """
你是一个顶级的Python编程专家。你的任务是根据用户的需求，编写一段完整、可直接运行的Python脚本。
- 你的代码必须是独立的，所有必要的导入都应包含在内。
- 不要使用任何需要额外安装的、不常见的第三方库，尽量使用Python标准库。
- 你的输出必须是且只能是纯粹的Python代码。不要包含任何注释、解释、或Markdown标记如 ```python。
"""

def create_code(task_description: str) -> str:
    """根据任务描述生成Python代码。"""
    print(f"正在为任务 '{task_description}' 请求LLM生成代码...")
    code = ask_llm(CODER_SYSTEM_PROMPT, task_description)
    return code
