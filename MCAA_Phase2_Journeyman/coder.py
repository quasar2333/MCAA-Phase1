# coder.py
from typing import Optional, Callable
from llm_interface import LLMProvider

CODER_SYSTEM_PROMPT = """
你是一位顶级的Python编程专家。你的任务是根据用户的需求，编写一段完整、可直接运行的Python脚本。
- 你的代码必须是独立的，所有必要的导入都应包含在内。
- 不要使用任何需要额外安装的、不常见的第三方库，尽量使用Python标准库。
- 你的输出必须是且只能是纯粹的Python代码。不要包含任何注释、解释、或Markdown标记如 ```python。
- 代码必须是高质量、健壮的，并处理常见的异常情况。
"""

MODIFIER_SYSTEM_PROMPT = """
你是一位代码重构和修改专家。你会收到一段现有的Python代码和一个修改请求。
你的任务是返回修改后的、完整的、可直接运行的新Python脚本。
- 你的输出必须是且只能是纯粹的Python代码。不要包含任何解释、注释或Markdown标记。
- 确保最终的代码是完整的，包含了所有必要的导入。
"""

def create_code(task_description: str, llm_provider: LLMProvider, log_func: Optional[Callable[[str], None]] = print) -> Optional[str]:
    """根据任务描述生成Python代码。"""
    if log_func: log_func(f"🤖 正在为任务 '{task_description}' 请求 '{llm_provider.get_name()}' 生成代码...")
    
    try:
        code = llm_provider.ask(CODER_SYSTEM_PROMPT, task_description)
        return _clean_code(code, log_func)
    except Exception as e:
        if log_func: log_func(f"❌ 代码生成时发生错误: {e}")
        return None

def modify_code(original_code: str, modification_request: str, llm_provider: LLMProvider, log_func: Optional[Callable[[str], None]] = print) -> Optional[str]:
    """根据请求修改现有代码。"""
    if log_func: log_func(f"🤖 正在根据请求 '{modification_request}' 修改现有代码...")

    user_prompt = f"【现有代码】:\n```python\n{original_code}\n```\n\n【修改要求】:\n{modification_request}"
    
    try:
        code = llm_provider.ask(MODIFIER_SYSTEM_PROMPT, user_prompt)
        return _clean_code(code, log_func)
    except Exception as e:
        if log_func: log_func(f"❌ 代码修改时发生错误: {e}")
        return None

def _clean_code(code: Optional[str], log_func: Optional[Callable[[str], None]] = print) -> Optional[str]:
    """清理LLM返回的代码，移除markdown等。"""
    if not code:
        return None
    
    if code.startswith("```python"):
        code = code[9:-3].strip()
    elif code.startswith("```"):
        code = code[3:-3].strip()

    if "Traceback" in code:
        if log_func: log_func(f"❌ 代码生成失败或返回了错误: {code}")
        return None
        
    return code
